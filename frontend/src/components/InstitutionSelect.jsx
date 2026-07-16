function InstitutionSelect({ institutions, value, onChange }) {
    return (
        <div>
            <label>Institution</label>

            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
            >
                <option value="">Select Institution</option>

                {institutions.map((institution) => (
                    <option
                        key={institution.id}
                        value={institution.id}
                    >
                        {institution.name}
                    </option>
                ))}
            </select>
        </div>
    );
}

export default InstitutionSelect;