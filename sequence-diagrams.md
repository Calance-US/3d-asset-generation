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

## Full Visualization Generation Flow (Async with Enhancement, Validation & Polling)

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant LLM
    participant Validator
    participant Database
    participant ThreeJS

    User->>Frontend: Enter prompt & subject
    User->>Frontend: (Optional) Click Enhance
    alt Enhancement Requested
        Frontend->>Backend: POST /enhance-prompt
        Backend->>LLM: Generate enhanced config
        LLM-->>Backend: Return enhanced config (JSON)
        Backend-->>Frontend: Return enhanced config
        Frontend-->>User: Display enhanced config
        User->>Frontend: Review/adjust config
    end
    User->>Frontend: Click Generate
    Frontend->>Backend: POST /async-visualizations/generate-async
    Backend-->>Frontend: Return { task_id }
    loop Poll for Status
        Frontend->>Backend: GET /async-visualizations/status/{task_id}
        Backend-->>Frontend: Return status, progress, current_stage
        alt Status = completed
            Frontend->>Backend: GET /async-visualizations/result/{task_id}
            Backend->>LLM: (If needed) Generate visualization HTML
            LLM-->>Backend: Return HTML with Three.js code
            Backend->>Validator: Validate HTML (syntax, scientific, realism, runtime)
            Validator-->>Backend: Return validation results
            alt Validation Success
                Backend->>Database: Save history entry
                Database-->>Backend: Confirm save
                Backend-->>Frontend: Return HTML & validation results
                Frontend->>ThreeJS: Initialize visualization
                ThreeJS-->>Frontend: Render 3D scene
                Frontend-->>User: Display visualization
            else Validation Error
                Backend-->>Frontend: Return HTML & validation errors
                Frontend-->>User: Display errors, allow fix/regenerate
            end
        else Status = failed
            Backend-->>Frontend: Return error details
            Frontend-->>User: Display error message
        else Status = running
            Note over Frontend: Continue polling
        end
    end
```

## Chat-Based Iterative Fixing Flow (Chat Session)

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend
    participant LLM
    participant Validator
    participant Database
    participant ThreeJS

    User->>Frontend: Load visualization (from history)
    Frontend-->>User: Display visualization & chat button
    User->>Frontend: Open chat, send feedback ("Make background darker")
    Frontend->>Backend: POST /chat/fix (history_entry_id, user_message)
    Backend->>Database: Get current HTML from history
    Backend->>LLM: Generate HTML fix (with user feedback & chat context)
    LLM-->>Backend: Return updated HTML
    Backend->>Validator: Validate updated HTML
    Validator-->>Backend: Return validation results
    Backend->>Database: Update history entry (overwrite HTML)
    Database-->>Backend: Confirm update
    Backend-->>Frontend: Return updated HTML, validation results, chat message
    Frontend-->>ThreeJS: Re-render visualization
    ThreeJS-->>Frontend: Render updated 3D scene
    Frontend-->>User: Display updated visualization & chat
    loop Further Iterations
        User->>Frontend: Send new chat message ("Add more lighting")
        Frontend->>Backend: POST /chat/message (chat_session_id, message)
        Backend->>Database: Get latest HTML
        Backend->>LLM: Generate new HTML fix
        LLM-->>Backend: Return updated HTML
        Backend->>Validator: Validate updated HTML
        Validator-->>Backend: Return validation results
        Backend->>Database: Update history entry
        Database-->>Backend: Confirm update
        Backend-->>Frontend: Return updated HTML, validation, chat message
        Frontend-->>ThreeJS: Re-render visualization
        ThreeJS-->>Frontend: Render updated 3D scene
        Frontend-->>User: Display updated visualization & chat
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
