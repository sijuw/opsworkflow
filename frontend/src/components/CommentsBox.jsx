function CommentsBox({ value, onChange }) {
    return (
        <div className="form-group">
            <label>Additional Comments</label>

            <textarea
                rows="5"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Optional..."
            />
        </div>
    );
}

export default CommentsBox;