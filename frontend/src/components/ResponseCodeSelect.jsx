function ResponseCodeSelect({ responseCodes, value, onChange }) {
    return (
        <div className="form-group">
            <label>Response Code</label>

            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
            >
                <option value="">Select Response Code</option>

                {responseCodes.map((code) => (
                    <option
                        key={code.code}
                        value={code.code}
                    >
                        {code.code} - {code.description}
                    </option>
                ))}
            </select>
        </div>
    );
}

export default ResponseCodeSelect;