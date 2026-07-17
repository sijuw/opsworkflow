import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

function CommentsBox({ value, onChange }) {
    return (
        <div className="flex flex-col space-y-2">
            <Label htmlFor="comments">Additional Comments</Label>
            <Textarea
                id="comments"
                placeholder="Optional context for the bank/institution..."
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="resize-none min-h-[100px]"
            />
        </div>
    );
}

export default CommentsBox;