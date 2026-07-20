import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

function AttachSamplesCheckbox({ checked, onChange }) {
    return (
        <div className="flex flex-row items-center space-x-3 pt-2">
            <Checkbox 
                id="attach-samples" 
                checked={checked} 
                onCheckedChange={onChange} 
                className="h-5 w-5 data-[state=checked]:bg-[#0056b3] data-[state=checked]:border-[#0056b3]"
            />
            {/* The Label component naturally prevents unwanted line breaks */}
            <Label 
                htmlFor="attach-samples" 
                className="text-sm font-medium leading-none cursor-pointer m-0 transition-colors hover:text-[#0056b3]"
            >
                Attach Sample Transactions
            </Label>
        </div>
    );
}

export default AttachSamplesCheckbox;