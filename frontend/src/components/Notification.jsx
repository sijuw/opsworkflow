function Notification({ type, message }) {
    if (!message) return null;

    return (
        <div className={`notification ${type}`}>
            {message}
        </div>
    );
}

export default Notification;