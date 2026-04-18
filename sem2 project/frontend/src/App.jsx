import { useState } from "react";
import {
    registerUser,
    createPost,
    getPosts,
    likePost,
    getNotifications
} from "./api/api";

function App() {
    const [posts, setPosts] = useState([]);
    const [notifications, setNotifications] = useState([]);

    async function handleRegister() {
        const username = prompt("username");
        const password = prompt("password");
        await registerUser(username, password);
        alert("User created");
    }

    async function loadPosts() {
        const data = await getPosts();
        setPosts(data);
    }

    async function handleCreatePost() {
        const author = prompt("author_id");
        const content = prompt("content");

        await createPost(Number(author), content);
        loadPosts();
    }

    async function handleLike(postId) {
        const userId = prompt("your user_id");
        await likePost(postId, userId);
        loadPosts();
    }

    async function loadNotifications() {
        const userId = prompt("user_id");
        const data = await getNotifications(userId);
        setNotifications(data);
    }

    return (
        <div style={{ padding: 20 }}>
            <h1>Social Network</h1>

            <button onClick={handleRegister}>Register</button>
            <button onClick={handleCreatePost}>Create Post</button>
            <button onClick={loadPosts}>Load Posts</button>
            <button onClick={loadNotifications}>Notifications</button>

            <hr />

            <h2>Posts</h2>
            {posts.map(p => (
                <div key={p.id} style={{ marginBottom: 10 }}>
                    <b>{p.content}</b>
                    <div>author: {p.author_id}</div>
                    <div>likes: {p.likes.length}</div>
                    <button onClick={() => handleLike(p.id)}>Like</button>
                </div>
            ))}

            <hr />

            <h2>Notifications</h2>
            {notifications.map(n => (
                <div key={n.id}>{n.message}</div>
            ))}
        </div>
    );
}

export default App;