import React, { useState } from 'react';
import { Button, TextField, Box, Typography, Paper } from '@mui/material';

function PromptConfig({ onSubmit, loading }) {
  const [config, setConfig] = useState({
    topic_name: '',
    key_concepts: '',
    education_level: 'High School',
    learning_objectives: '',
    interactive_features: '',
    components: [],
    materials: [],
    lights: [],
    interactive_description: '',
    animated_elements: '',
    narration_texts: []
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(config);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, bgcolor: 'background.paper' }}>
      <Typography variant="h6" gutterBottom>
        Configuration
      </Typography>
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Topic Name"
          value={config.topic_name}
          onChange={(e) => setConfig({ ...config, topic_name: e.target.value })}
          margin="normal"
        />
        <TextField
          fullWidth
          label="Key Concepts"
          value={config.key_concepts}
          onChange={(e) => setConfig({ ...config, key_concepts: e.target.value })}
          margin="normal"
        />
        <TextField
          fullWidth
          label="Learning Objectives"
          value={config.learning_objectives}
          onChange={(e) => setConfig({ ...config, learning_objectives: e.target.value })}
          margin="normal"
        />
        <TextField
          fullWidth
          label="Interactive Features"
          value={config.interactive_features}
          onChange={(e) => setConfig({ ...config, interactive_features: e.target.value })}
          margin="normal"
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={loading}
          sx={{ mt: 2 }}
        >
          {loading ? 'Generating...' : 'Generate'}
        </Button>
      </Box>
    </Paper>
  );
}

export default PromptConfig; 