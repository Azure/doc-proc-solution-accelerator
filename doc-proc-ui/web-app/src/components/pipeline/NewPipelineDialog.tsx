
import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Save } from "lucide-react";

interface NewPipelineDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (pipeline: { name: string; description: string }) => Promise<void>;
}

const NewPipelineDialog = ({ isOpen, onClose, onSave }: NewPipelineDialogProps) => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!formData.name.trim()) return;
    
    try {
      setSaving(true);
      await onSave(formData);
      setFormData({ name: '', description: '' });
    } catch (error) {
      console.error('Error creating pipeline:', error);
      // Keep dialog open on error
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Pipeline</DialogTitle>
          <DialogDescription>
            Create a new document processing pipeline
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <Label htmlFor="pipeline-name">Pipeline Name</Label>
            <Input 
              id="pipeline-name" 
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Enter pipeline name"
            />
          </div>
          
          <div>
            <Label htmlFor="pipeline-description">Description</Label>
            <Textarea 
              id="pipeline-description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Enter pipeline description"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose} disabled={saving}>
              Cancel
            </Button>
            <Button 
              onClick={handleSave}
              disabled={!formData.name.trim() || saving}
            >
              <Save className="h-4 w-4 mr-2" />
              {saving ? 'Creating...' : 'Create Pipeline'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default NewPipelineDialog;