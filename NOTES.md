## Steps
### 1. Convert JSON to META TYPES STRUCTURE

`meta_type := Dict[str, meta_type] | DynamicType[meta_type, ...] | type`
- Dict mean it's an object that will be constructed at step 3
- DynamicType is complex type based on some other meta types.
    It probably will be extended at step 2 and replaced with type from typing package at step 3
- Type is one json-serializable classes (int, str, bool, etc.)

### 2. Merge data variants

### 3. Create and register models

### 4. Merge models and extract common ones

### 5. Save models as python code or OpenAPI spec

