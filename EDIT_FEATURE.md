# Theme Edit Feature

## Overview
Added the ability to edit existing themes directly from the TUI by clicking an edit icon (✎) next to each theme.

## Implementation

### 1. GradientPanel (gradient.py)
- **Added edit icon**: Each theme now displays a blue ✎ icon on the far right
- **Added `ThemeEditRequested` message**: Posted when edit icon is clicked
- **Click handling**: 
  - Click on theme name/gradient → Apply theme
  - Click on edit icon (far right) → Load theme for editing

### 2. ThemeCreator (theme_creator.py)
- **Added editing mode**: Tracks `editing_theme_key` to know if editing vs. creating
- **Added `load_theme_for_editing()` method**: 
  - Extracts first, middle, and last colors from 22-color gradient
  - Populates the creator fields with theme data
  - Shows "Editing: [theme name]" placeholder
- **Modified `action_save_theme()`**:
  - Detects editing mode
  - Shows "Updating..." vs "Saving..." message
  - Overwrites existing theme when editing
  - Shows "Updated" vs "Saved" success message
- **Modified `action_clear()`**: Exits editing mode

### 3. Main App (app.py)
- **Added handler**: `on_gradient_panel_theme_edit_requested()`
- Connects edit requests from gradient panel to theme creator

## User Workflow

1. **View themes**: All themes listed with edit icon (✎) on right
2. **Click edit icon**: Theme's 3 key colors loaded into creator
3. **Modify colors**: Adjust gradient using color inputs
4. **Preview**: Live gradient preview updates
5. **Save**: Press [S] or click Save button
6. **Result**: Original theme overwritten with new colors

## Technical Details

- Editing preserves the original theme key (URL-safe identifier)
- Only the theme name and colors are editable
- The 3-color input is expanded to 22-color gradient via `generate-colors.py`
- Daemon automatically reloads theme database when `themes.json` changes
- No restart required

## Example

**Before Edit:**
```
pink: #ff006e, #ff006e, #ff006e (all same color)
```

**After Clicking Edit Icon:**
- Theme creator loads: name="Pink", colors=("#ff006e", "#ff006e", "#ff006e")
- User modifies to: "#ff0099", "#cc00ff", "#9900ff" (pink to purple gradient)
- User presses Save
- `pink` theme updated in database with new 22-color gradient
- Daemon detects change and reloads automatically
