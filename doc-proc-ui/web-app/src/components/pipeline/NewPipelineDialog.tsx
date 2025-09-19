
import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Save, AlertCircle } from "lucide-react";

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
  const [error, setError] = useState<string>('');

  const handleClose = () => {
    setError(''); // Clear error when closing
    onClose();
  };

  const handleInputChange = (field: 'name' | 'description', value: string) => {
    setFormData({ ...formData, [field]: value });
    if (error) setError(''); // Clear error when user starts typing
  };

  const handleSave = async () => {
    if (!formData.name.trim()) return;
    
    try {
      setSaving(true);
      setError(''); // Clear any previous errors
      await onSave(formData);
      setFormData({ name: '', description: '' });
    } catch (error: any) {
      console.error('Error creating pipeline:', error);

      // Extract error message from API response or use a fallback
      let errorMessage = 'Failed to create pipeline. Please try again.';
      
      if (error?.details) {
        errorMessage = error.details;
      } else if (error?.error) {
        errorMessage = error.error;
      } else if (error?.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      setError(errorMessage);
      // Keep dialog open on error
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Pipeline</DialogTitle>
          <DialogDescription>
            Create a new document processing pipeline
          </DialogDescription>
        </DialogHeader>
        
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error}
            </AlertDescription>
          </Alert>
        )}
        
        <div className="space-y-4">
          <div>
            <Label htmlFor="pipeline-name">Pipeline Name</Label>
            <Input 
              id="pipeline-name" 
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Enter pipeline name"
            />
          </div>
          
          <div>
            <Label htmlFor="pipeline-description">Description</Label>
            <Textarea 
              id="pipeline-description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Enter pipeline description"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={handleClose} disabled={saving}>
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