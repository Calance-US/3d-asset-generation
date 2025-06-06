# 3D Visualization System Sequence Diagrams

## Basic Visualization Generation Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant LLM
    participant ThreeJS

    User->>Frontend: Enter prompt & subject
    User->>Frontend: Configure visualization settings
    User->>Frontend: Click Generate
    Frontend->>Backend: POST /generate
    Note over Frontend,Backend: Request includes:<br/>- topic<br/>- provider<br/>- subject<br/>- config
    Backend->>LLM: Generate visualization code
    LLM-->>Backend: Return Three.js code
    Backend->>Backend: Process & validate code
    Backend-->>Frontend: Return HTML with Three.js code
    Frontend->>ThreeJS: Initialize visualization
    ThreeJS-->>Frontend: Render 3D scene
    Frontend-->>User: Display visualization
```

## History Management Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Database

    User->>Frontend: View History
    Frontend->>Backend: GET /history
    Backend->>Database: Query history entries
    Database-->>Backend: Return entries
    Backend-->>Frontend: Return history data
    Frontend-->>User: Display history list

    User->>Frontend: Select history entry
    Frontend->>Backend: GET /history/{id}/html
    Backend->>Database: Query entry HTML
    Database-->>Backend: Return HTML
    Backend-->>Frontend: Return visualization HTML
    Frontend-->>User: Display selected visualization
```

## Prompt Enhancement Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant LLM

    User->>Frontend: Enter initial prompt
    User->>Frontend: Click Enhance
    Frontend->>Backend: POST /enhance-prompt
    Note over Frontend,Backend: Request includes:<br/>- user prompt<br/>- subject<br/>- LLM Provider
    Backend ->> Backend: Generate an enhancement System prompt <br/>using User prompt and subject
    Backend->>LLM: System prompt
    LLM-->>Backend: Return enhanced Json data (Config data)
    Backend-->>Frontend: Return enhanced prompt & config
    Frontend-->>User: Display enhanced configuration
    User->>Frontend: Review & adjust if needed
    User->>Frontend: Click Generate
    Frontend->>Backend: POST /generate
    Note over Frontend,Backend: Request includes enhanced config
    Backend ->> Backend: Generate a System prompt <br/>using enhanced config <br/>from prompt template
    Backend->>LLM: Generate visualization code
    LLM-->>Backend: Return Html with Three.js code
    Backend->>Backend: Process & validate Html
    Backend-->>Frontend: Return visualization Html
    Frontend-->>User: Display visualization
```

## Error Handling Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant LLM

    User->>Frontend: Submit generation request
    Frontend->>Backend: POST /generate
    Backend->>LLM: Generate visualization
    alt Generation Success
        LLM-->>Backend: Return valid code
        Backend-->>Frontend: Return HTML
        Frontend-->>User: Display visualization
    else Generation Error
        LLM-->>Backend: Return error
        Backend-->>Frontend: Return error details
        Frontend-->>User: Display error message
    else Validation Error
        Backend->>Backend: Validate code
        Backend-->>Frontend: Return validation error
        Frontend-->>User: Display validation error
    end
```

## Configuration Management Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant Database

    User->>Frontend: Modify configuration
    Note over User,Frontend: Changes include:<br/>- renderer settings<br/>- materials<br/>- lights<br/>- components
    Frontend->>Frontend: Validate configuration
    alt Valid Configuration
        Frontend->>Backend: POST /generate
        Backend->>Database: Store configuration
        Database-->>Backend: Confirm storage
        Backend-->>Frontend: Return visualization
        Frontend-->>User: Display updated visualization
    else Invalid Configuration
        Frontend-->>User: Display validation errors
    end
```

## Notes

1. **Renderer Configuration**
   - Uses Three.js v0.155.0
   - Default renderer settings:
     - `antialias: true`
     - `shadowMapEnabled: true`
     - `shadowMapType: "PCFSoftShadowMap"`
     - `outputColorSpace: "SRGBColorSpace"`
     - `toneMapping: "ACESFilmicToneMapping"`
     - `toneMappingExposure: 1.0`

2. **Required Fields**
   - `three_js_url`
   - `orbit_controls_url`
   - `camera_controls`
   - `curve_points`
   - `animation_speed`
   - `tts_language`
   - `tts_rate`
   - `tts_pitch`

3. **Error Handling**
   - Validation errors for missing fields
   - Generation errors from LLM
   - Runtime errors in Three.js code
   - Network errors
   - Database errors 