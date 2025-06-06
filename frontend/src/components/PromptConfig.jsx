import React, { useState } from 'react';
import { Button, TextField, Select, MenuItem, FormControl, InputLabel, Box, Typography, Paper } from '@mui/material';

const PromptConfig = ({ onSubmit, loading }) => {
  const [config, setConfig] = useState({
    topic_name: '',
    key_concepts: '',
    education_level: '',
    learning_objectives: '',
    interactive_features: '',
    components: [{ component_name: '', component_description: '' }],
    materials: [{ material_name: '', color: '0x808080', metalness: 0.5, roughness: 0.5 }],
    lights: [{ light_type: '', light_class: '', light_color: '0xffffff', intensity: 0.5 }],
    camera_controls: '',
    interactive_description: '',
    animated_elements: '',
    narration_texts: ['']
  });

  const handleChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayChange = (field, index, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => 
        i === index ? { ...item, ...value } : item
      )
    }));
  };

  const addArrayItem = (field, template) => {
    setConfig(prev => ({
      ...prev,
      [field]: [...prev[field], template]
    }));
  };

  const removeArrayItem = (field, index) => {
    setConfig(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(config);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" gutterBottom>
        Configure 3D Visualization
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Basic Information */}
        <TextField
          label="Topic Name"
          value={config.topic_name}
          onChange={(e) => handleChange('topic_name', e.target.value)}
          required
          fullWidth
        />
        
        <TextField
          label="Key Concepts"
          value={config.key_concepts}
          onChange={(e) => handleChange('key_concepts', e.target.value)}
          required
          fullWidth
          multiline
          rows={2}
        />
        
        <TextField
          label="Education Level"
          value={config.education_level}
          onChange={(e) => handleChange('education_level', e.target.value)}
          required
          fullWidth
        />
        
        <TextField
          label="Learning Objectives"
          value={config.learning_objectives}
          onChange={(e) => handleChange('learning_objectives', e.target.value)}
          required
          fullWidth
          multiline
          rows={2}
        />
        
        <TextField
          label="Interactive Features"
          value={config.interactive_features}
          onChange={(e) => handleChange('interactive_features', e.target.value)}
          required
          fullWidth
        />

        {/* Components Section */}
        <Typography variant="h6" gutterBottom>
          Components
        </Typography>
        {config.components.map((component, index) => (
          <Box key={index} sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label="Component Name"
              value={component.component_name}
              onChange={(e) => handleArrayChange('components', index, { component_name: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Description"
              value={component.component_description}
              onChange={(e) => handleArrayChange('components', index, { component_description: e.target.value })}
              required
              fullWidth
            />
            <Button 
              onClick={() => removeArrayItem('components', index)}
              color="error"
              disabled={config.components.length === 1}
            >
              Remove
            </Button>
          </Box>
        ))}
        <Button 
          onClick={() => addArrayItem('components', { component_name: '', component_description: '' })}
          variant="outlined"
        >
          Add Component
        </Button>

        {/* Materials Section */}
        <Typography variant="h6" gutterBottom>
          Materials
        </Typography>
        {config.materials.map((material, index) => (
          <Box key={index} sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label="Material Name"
              value={material.material_name}
              onChange={(e) => handleArrayChange('materials', index, { material_name: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Color (hex)"
              value={material.color}
              onChange={(e) => handleArrayChange('materials', index, { color: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Metalness"
              type="number"
              value={material.metalness}
              onChange={(e) => handleArrayChange('materials', index, { metalness: parseFloat(e.target.value) })}
              required
              fullWidth
              inputProps={{ min: 0, max: 1, step: 0.1 }}
            />
            <TextField
              label="Roughness"
              type="number"
              value={material.roughness}
              onChange={(e) => handleArrayChange('materials', index, { roughness: parseFloat(e.target.value) })}
              required
              fullWidth
              inputProps={{ min: 0, max: 1, step: 0.1 }}
            />
            <Button 
              onClick={() => removeArrayItem('materials', index)}
              color="error"
              disabled={config.materials.length === 1}
            >
              Remove
            </Button>
          </Box>
        ))}
        <Button 
          onClick={() => addArrayItem('materials', { 
            material_name: '', 
            color: '0x808080', 
            metalness: 0.5, 
            roughness: 0.5 
          })}
          variant="outlined"
        >
          Add Material
        </Button>

        {/* Lights Section */}
        <Typography variant="h6" gutterBottom>
          Lights
        </Typography>
        {config.lights.map((light, index) => (
          <Box key={index} sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label="Light Type"
              value={light.light_type}
              onChange={(e) => handleArrayChange('lights', index, { light_type: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Light Class"
              value={light.light_class}
              onChange={(e) => handleArrayChange('lights', index, { light_class: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Color (hex)"
              value={light.light_color}
              onChange={(e) => handleArrayChange('lights', index, { light_color: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Intensity"
              type="number"
              value={light.intensity}
              onChange={(e) => handleArrayChange('lights', index, { intensity: parseFloat(e.target.value) })}
              required
              fullWidth
              inputProps={{ min: 0, max: 2, step: 0.1 }}
            />
            <Button 
              onClick={() => removeArrayItem('lights', index)}
              color="error"
              disabled={config.lights.length === 1}
            >
              Remove
            </Button>
          </Box>
        ))}
        <Button 
          onClick={() => addArrayItem('lights', { 
            light_type: '', 
            light_class: '', 
            light_color: '0xffffff', 
            intensity: 0.5 
          })}
          variant="outlined"
        >
          Add Light
        </Button>

        {/* Camera and Interaction */}
        <TextField
          label="Camera Controls"
          value={config.camera_controls}
          onChange={(e) => handleChange('camera_controls', e.target.value)}
          required
          fullWidth
        />
        
        <TextField
          label="Interactive Description"
          value={config.interactive_description}
          onChange={(e) => handleChange('interactive_description', e.target.value)}
          required
          fullWidth
          multiline
          rows={2}
        />
        
        <TextField
          label="Animated Elements"
          value={config.animated_elements}
          onChange={(e) => handleChange('animated_elements', e.target.value)}
          required
          fullWidth
        />

        {/* Narration Texts */}
        <Typography variant="h6" gutterBottom>
          Narration Texts
        </Typography>
        {config.narration_texts.map((text, index) => (
          <Box key={index} sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label={`Narration ${index + 1}`}
              value={text}
              onChange={(e) => {
                const newTexts = [...config.narration_texts];
                newTexts[index] = e.target.value;
                handleChange('narration_texts', newTexts);
              }}
              required
              fullWidth
              multiline
              rows={2}
            />
            <Button 
              onClick={() => removeArrayItem('narration_texts', index)}
              color="error"
              disabled={config.narration_texts.length === 1}
            >
              Remove
            </Button>
          </Box>
        ))}
        <Button 
          onClick={() => addArrayItem('narration_texts', '')}
          variant="outlined"
        >
          Add Narration
        </Button>

        {/* Submit Button */}
        <Button 
          type="submit" 
          variant="contained" 
          color="primary"
          disabled={loading}
          sx={{ mt: 2 }}
        >
          {loading ? 'Generating...' : 'Generate Visualization'}
        </Button>
      </Box>
    </Paper>
  );
};

export default PromptConfig; 