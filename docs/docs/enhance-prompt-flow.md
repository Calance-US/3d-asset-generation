# Enhance Prompt Flow

This document describes the sequence of interactions when a user enhances a prompt in the 3D Educational Visualization Platform.

## Overview

The enhance prompt flow allows users to take a basic topic description and automatically generate a detailed configuration with educational content, interactive features, and rendering settings.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (Generator.jsx)
    participant B as Backend API
    participant PG as Prompt Generator
    participant PS as Prompt Selector
    participant LLM as AI Provider (OpenAI/Gemini/Ollama)
    participant DB as Database

    Note over U,DB: User initiates prompt enhancement
    U->>F: Enter basic topic prompt
    U->>F: Click "Enhance" button
    
    Note over F: Frontend validation
    F->>F: Validate prompt is not empty
    F->>F: Set enhancing state to true
    
    Note over F,B: Send enhancement request
    F->>B: POST /prompt/enhance-prompt
    Note right of F: Payload: {topic, provider, subject}
    
    Note over B: Backend processing
    B->>PS: Select appropriate prompt template
    PS->>PS: Choose template based on subject/topic
    
    B->>PG: Generate enhanced configuration
    PG->>LLM: Send enhancement prompt
    Note right of PG: Template includes:<br/>- Topic analysis<br/>- Educational requirements<br/>- Interactive features<br/>- Rendering settings
    
    LLM->>PG: Return enhanced configuration
    Note right of LLM: Response includes:<br/>- Key concepts<br/>- Learning objectives<br/>- Interactive features<br/>- Scene description<br/>- Components, materials, lights<br/>- Renderer settings
    
    PG->>B: Return structured configuration
    B->>F: Return enhanced configuration
    Note right of B: Response: {<br/>  topic_name, key_concepts,<br/>  education_level, learning_objectives,<br/>  interactive_features, components,<br/>  materials, lights, scene_description,<br/>  intro_narration_texts,<br/>  supporting_narration_texts,<br/>  renderer: {...}<br/>}
    
    Note over F: Update frontend state
    F->>F: Update config state with enhanced data
    F->>F: Set enhancing state to false
    
    Note over U: User sees enhanced configuration
    F->>U: Display enhanced configuration
    Note right of F: Shows:<br/>- Key concepts<br/>- Learning objectives<br/>- Interactive features<br/>- Scene description<br/>- Renderer settings
    
    Note over U: User can now generate visualization
    U->>F: Click "Generate Scene" button
```

## Key Components

### Frontend (Generator.jsx)
- **handleEnhance()**: Main function that orchestrates the enhancement flow
- **State Management**: Manages `enhancing` state and `config` updates
- **Error Handling**: Displays errors if enhancement fails

### Backend API (/prompt/enhance-prompt)
- **Prompt Selector**: Chooses appropriate template based on subject
- **Prompt Generator**: Creates detailed enhancement prompt
- **AI Integration**: Sends request to configured AI provider
- **Response Parsing**: Converts AI response to structured configuration

### AI Provider Integration
- **OpenAI**: Uses GPT-4 for enhancement
- **Gemini**: Uses Google's Gemini model
- **Ollama**: Uses local Ollama instance

## Configuration Structure

The enhanced configuration includes:

```json
{
  "topic_name": "Ohm's Law Electric Circuit",
  "key_concepts": ["Voltage", "Current", "Resistance", "Ohm's Law"],
  "education_level": "High School",
  "learning_objectives": [
    "Understand the relationship between voltage, current, and resistance",
    "Visualize how changing resistance affects current flow"
  ],
  "interactive_features": [
    "Adjustable voltage source",
    "Variable resistor",
    "Real-time current measurement"
  ],
  "components": [
    {
      "type": "voltage_source",
      "position": {"x": 0, "y": 0, "z": 0},
      "properties": {"voltage": 12}
    }
  ],
  "materials": [...],
  "lights": [...],
  "scene_description": "Interactive 3D electric circuit demonstrating Ohm's Law...",
  "intro_narration_texts": ["Welcome to our Ohm's Law demonstration..."],
  "supporting_narration_texts": ["As we increase the voltage..."],
  "renderer": {
    "antialias": true,
    "shadowMapEnabled": true,
    "toneMapping": "ACESFilmicToneMapping"
  }
}
```

## Error Handling

- **Empty Prompt**: Frontend prevents enhancement of empty prompts
- **AI Provider Errors**: Backend handles API failures gracefully
- **Invalid Response**: Backend validates AI response structure
- **Network Issues**: Frontend shows user-friendly error messages

## Benefits

1. **Reduced User Effort**: Users don't need to manually configure complex settings
2. **Educational Accuracy**: AI ensures educational content is appropriate
3. **Consistent Quality**: Standardized enhancement process
4. **Interactive Features**: Automatically suggests relevant interactive elements
5. **Professional Rendering**: Optimized renderer settings for educational content 