# tests/test_business_logic.py
import asyncio
import importlib.util
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class _FakeConfluentProducer:
    def __init__(self, *args, **kwargs): pass
    def produce(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass
class _FakePasswordHasher:
    def hash(self, password): return "$argon2$" + password
    def verify(self, password_hash, password):
        if password_hash != "$argon2$" + password: raise ValueError("bad password")
        return True
def _jwt_encode(payload, secret, algorithm=None):
    import base64, json
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
def _jwt_decode(token, secret, algorithms=None):
    import base64, json
    return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
sys.modules.setdefault("confluent_kafka", SimpleNamespace(Producer=_FakeConfluentProducer, Consumer=object))
sys.modules.setdefault("argon2", SimpleNamespace(PasswordHasher=_FakePasswordHasher))
sys.modules.setdefault("jose", SimpleNamespace(JWTError=Exception, jwt=SimpleNamespace(encode=_jwt_encode, decode=_jwt_decode)))
sys.modules.setdefault("redis", SimpleNamespace(asyncio=SimpleNamespace(Redis=object)))
sys.modules.setdefault("redis.asyncio", SimpleNamespace(Redis=object))

def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

user_schemas = load("schemas", "user-service/schemas.py")
load("repositories", "user-service/repositories.py")
user_services = load("user_services", "user-service/services.py")
playlist_schemas = load("playlist_schemas", "playlist-service/schemas.py")
sys.modules["schemas"] = playlist_schemas
playlist_repos = load("playlist_repositories", "playlist-service/repositories.py")
sys.modules["repositories"] = playlist_repos
sys.modules.setdefault("spotify", SimpleNamespace())
load("spotify.client", "playlist-service/spotify/client.py")
playlist_services = load("playlist_services", "playlist-service/services.py")
worker_handler = load("worker_playlist_handler", "worker-service/handlers/playlist.py")
from shared.security import create_token, decode_token, hash_password, verify_password

class FakeSession:
    def __init__(self): self.added=[]; self.deleted=[]; self.commits=0
    def add(self, obj): self.added.append(obj)
    async def flush(self): pass
    async def commit(self): self.commits += 1
    async def rollback(self): pass
    async def refresh(self, obj, attrs=None): pass
    async def delete(self, obj): self.deleted.append(obj)
class FakeProducer:
    def __init__(self): self.events=[]
    async def publish(self, topic, key, event): self.events.append((topic, key, event))
class FakeUserRepo:
    def __init__(self, session): pass
    async def by_email_or_username(self, value): return None
    async def create(self, email, username, password_hash): return SimpleNamespace(id=uuid.uuid4(), email=email, username=username, password_hash=password_hash, profile_data={}, created_at="now", updated_at="now")
class FakeCache:
    def __init__(self): self.store={}; self.deleted=[]; self.ttl=None
    async def get(self, key): return self.store.get(key)
    async def set(self, key, value, ex=None): self.store[key]=value; self.ttl=ex
    async def delete(self, key): self.deleted.append(key); self.store.pop(key, None)
class FakePlaylistRepo:
    def __init__(self, session): self.playlist=SimpleNamespace(id=uuid.uuid4(), owner_id=uuid.uuid4(), title="mix", description="", is_public=False, created_at="now", updated_at="now", tracks=[]); self.track=None
    async def create(self, owner_id, title, description, is_public): self.playlist.owner_id=uuid.UUID(owner_id); self.playlist.title=title; self.playlist.description=description; self.playlist.is_public=is_public; return self.playlist
    async def get(self, playlist_id): return self.playlist
    async def get_track(self, playlist_id, track_id): return self.track
    async def list_for_user(self, user_id, visibility): return [self.playlist]

def test_register_creates_user_and_kafka_event(monkeypatch):
    async def run():
        monkeypatch.setattr(user_services, "UserRepository", FakeUserRepo)
        producer = FakeProducer()
        user_id, tokens = await user_services.UserServiceLogic(FakeSession(), producer).register(user_schemas.RegisterIn(email="a@example.com", username="alice", password="password123"))
        assert uuid.UUID(user_id)
        assert decode_token(tokens.access_token)["typ"] == "access"
        assert producer.events[0][0] == "user.events"
        assert producer.events[0][2]["event_type"] == "user.registered"
    asyncio.run(run())

def test_login_rejects_invalid_credentials(monkeypatch):
    async def run():
        class Repo(FakeUserRepo):
            async def by_email_or_username(self, value): return SimpleNamespace(password_hash=hash_password("right"), id=uuid.uuid4())
        monkeypatch.setattr(user_services, "UserRepository", Repo)
        with pytest.raises(user_services.ServiceError):
            await user_services.UserServiceLogic(FakeSession()).login(user_schemas.LoginIn(login="alice", password="wrong"))
    asyncio.run(run())

def test_register_schema_validates_email_and_password():
    with pytest.raises(ValidationError): user_schemas.RegisterIn(email="bad", username="ab", password="short")

def test_argon2_password_hashing_roundtrip():
    hashed = hash_password("password123")
    assert hashed.startswith("$argon2") and verify_password("password123", hashed) and not verify_password("bad", hashed)

def test_jwt_contains_subject_and_jti():
    payload = decode_token(create_token("user-1", "access", 60))
    assert payload["sub"] == "user-1" and payload["typ"] == "access" and payload["jti"]

def test_create_playlist_emits_event(monkeypatch):
    async def run():
        monkeypatch.setattr(playlist_services, "PlaylistRepository", FakePlaylistRepo)
        owner = str(uuid.uuid4()); producer = FakeProducer()
        playlist = await playlist_services.PlaylistServiceLogic(FakeSession(), producer).create(owner, playlist_schemas.PlaylistCreate(title="Road", is_public=True))
        assert playlist.title == "Road" and producer.events[0][2]["event_type"] == "playlist.created"
    asyncio.run(run())

def test_get_playlist_sets_redis_cache(monkeypatch):
    async def run():
        owner = str(uuid.uuid4())
        class Repo(FakePlaylistRepo):
            def __init__(self, session): super().__init__(session); self.playlist.owner_id = uuid.UUID(owner)
        monkeypatch.setattr(playlist_services, "PlaylistRepository", Repo)
        cache = FakeCache(); await playlist_services.PlaylistServiceLogic(FakeSession(), cache=cache).get(str(uuid.uuid4()), owner)
        assert cache.ttl == 600 and len(cache.store) == 1
    asyncio.run(run())

def test_add_duplicate_track_raises_conflict(monkeypatch):
    async def run():
        class Repo(FakePlaylistRepo):
            async def get_track(self, playlist_id, track_id): return SimpleNamespace(spotify_track_id=track_id)
        monkeypatch.setattr(playlist_services, "PlaylistRepository", Repo)
        service = playlist_services.PlaylistServiceLogic(FakeSession())
        with pytest.raises(playlist_services.ServiceError) as exc:
            await service.add_track(str(service.repo.playlist.id), str(service.repo.playlist.owner_id), playlist_schemas.TrackAdd(spotify_track_id="s1"))
        assert exc.value.message == "track already exists"
    asyncio.run(run())

def test_update_public_invalidates_cache_and_emits(monkeypatch):
    async def run():
        monkeypatch.setattr(playlist_services, "PlaylistRepository", FakePlaylistRepo)
        cache = FakeCache(); producer = FakeProducer(); service = playlist_services.PlaylistServiceLogic(FakeSession(), producer, cache=cache)
        pid = str(service.repo.playlist.id)
        updated = await service.update(pid, str(service.repo.playlist.owner_id), playlist_schemas.PlaylistUpdate(is_public=True))
        assert updated.is_public is True and f"playlist:{pid}" in cache.deleted and producer.events[0][2]["event_type"] == "playlist.updated"
    asyncio.run(run())

def test_worker_playlist_event_invalidates_cache():
    async def run():
        cache = FakeCache(); await worker_handler.invalidate_playlist_cache(cache, {"event_type": "playlist.track.added", "aggregate_id": "p1"})
        assert cache.deleted == ["playlist:p1"]
    asyncio.run(run())

def test_list_private_for_other_user_forces_public(monkeypatch):
    async def run():
        seen = {}
        class Repo(FakePlaylistRepo):
            async def list_for_user(self, user_id, visibility): seen["visibility"] = visibility; return []
        monkeypatch.setattr(playlist_services, "PlaylistRepository", Repo)
        await playlist_services.PlaylistServiceLogic(FakeSession()).list_user(str(uuid.uuid4()), str(uuid.uuid4()), "private")
        assert seen["visibility"] == "public"
    asyncio.run(run())
