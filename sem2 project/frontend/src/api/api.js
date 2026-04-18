const API = "http://127.0.0.1:8000";

// USERS
export async function registerUser(username, password) {
    return fetch(`${API}/users/register`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ username, password })
    });
}

// POSTS
export async function createPost(author_id, content) {
    return fetch(`${API}/posts/`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ author_id, content })
    });
}

export async function getPosts() {
    return fetch(`${API}/posts/`).then(r => r.json());
}

export async function likePost(postId, userId) {
    return fetch(`${API}/posts/${postId}/like/${userId}`, {
        method: "POST"
    });
}

// NOTIFICATIONS
export async function getNotifications(userId) {
    return fetch(`${API}/notifications/user/${userId}`)
        .then(r => r.json());
}