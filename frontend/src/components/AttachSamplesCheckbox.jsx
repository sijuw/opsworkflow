function AttachSamplesCheckbox({ checked, onChange }) {
    return (
        <div>
            <label>
                <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => onChange(e.target.checked)}
                />

                Attach Sample Transactions
            </label>
        </div>
    );
}

export default AttachSamplesCheckbox;