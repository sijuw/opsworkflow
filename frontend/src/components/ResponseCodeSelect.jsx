import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

function ResponseCodeSelect({ responseCodes, value, onChange }) {
    return (
        <div className="flex flex-col space-y-2">
            <Label htmlFor="response-code-select">Response Code</Label>
            
            <Select 
                value={value?.toString()} 
                onValueChange={onChange}
            >
                <SelectTrigger id="response-code-select" className="w-full">
                    <SelectValue placeholder="Select Response Code" />
                </SelectTrigger>
                
                <SelectContent>
                    {responseCodes.map((code) => (
                        <SelectItem
                            key={code.code}
                            // Shadcn requires the value to be a string
                            value={code.code.toString()}
                        >
                            {code.code} - {code.description}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
        </div>
    );
}

export default ResponseCodeSelect;