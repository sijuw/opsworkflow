import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

function InstitutionSelect({ institutions, value, onChange }) {
    return (
        <div className="flex flex-col space-y-2">
            <Label htmlFor="institution-select">Institution</Label>
            
            <Select 
                value={value?.toString()} 
                onValueChange={onChange}
            >
                <SelectTrigger id="institution-select" className="w-full">
                    <SelectValue placeholder="Select Institution" />
                </SelectTrigger>
                
                <SelectContent>
                    {institutions.map((institution) => (
                        <SelectItem
                            key={institution.id}
                            /* Shadcn expects values to be strings */
                            value={institution.id.toString()}
                        >
                            {institution.name}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
        </div>
    );
}

export default InstitutionSelect;