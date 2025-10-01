# A Guide to Theming in Perspective

## Overview

Theming in Perspective allows designers to customize the look-and-feel (**not layout**) of their Perspective projects at a broad level. A projects active theme is defined in a project's session properties.  Where applicable, any styles applied using Perspective Style Classes or inline styles within the Designer should still override anything inherited from a theme.  It is possible to work around this rule, but that is not something we would recommend. Theming is considered an advanced feature of Perspective.  As such, we operate under the assumption that anyone altering these files has some knowledge of CSS. By making use of CSS variables, imports, and descriptive class selectors, you will find that we have provided features and structure to help alleviate some of the frustrations inherent to managing large amounts of CSS.

## Available Themes

As of writing this, the following themes have been made available to you, by us.  This list may grow with time.

- `light` (base theme)
- `light-warm`
- `light-cool`
- `dark`
- `dark-warm`
- `dark-cool`

## Structure

The entry point to your themes live at the root of the `themes` directory.  Each entry point will be used to populate the list of themes available in Perspective. An entry point must be a valid css file.

Changes to any files within this directory will trigger the reprocessing of any requested themes.  Only themes that have been requested will be reprocessed.

Before getting started, we recommend that you familiarize yourself with the structure of one of our provided themes.

** **IMPORTANT** **

Both the `light` and `dark` themes are owned and maintained by Inductive Automation.  This means that any changes to the `light` and `dark` folders will be discarded on startup.  This rule pertains to the `light` and `dark` folders only.

Note, changes to `light.css` and `dark.css` entry points will not be discarded on startup to provide you with the ability to override certain rules declared and inherited from the corresponding theme directories (see section on overriding or adapting themes).

## Features

### CSS Variables

CSS variables have a central role in theme authoring.  We recommend leveraging this built in feature of CSS to aid in modular theme development and ease frustrations of long term maintenance.  We use CSS variables throughout our theme stylesheets, so whenever there may be a need to change something like a color, it only needs to be changed in a single file.

Declaring variables:

`--corporateColor: #FF5D00;`

Using variables:

`background-color: var(--corporateColor);`

Variables can also be used in the Designer's property editor as the value of a components style property.  Assuming that the variable exists, of course.  Simply specify the variables name as the style property value:

`backgroundColor: --corporateColor`

### Descriptive CSS Classes

Component authors specify unique CSS class selectors that give you direct access to the styling of particular elements.  Each class selector is unique enough to prevent clashing and descriptive enough to minimize any guessing surrounding its dedicated purpose.  We follow a standard naming convention called ABEM (Atomic Block Element Modifier).

Convention in a nutshell:

`atomicPrefix_blockName__elementName--modifierName`

In use:

`ia_cylindricalTankComponent__liquid--animation`

Keep in mind that these unique classes give you direct access to specific elements.  You can find a list of available selectors, and their defined rules, in their respective files.  If you can not find the selector you need, then it is likely not defined.  You may either request it or use one of the many other ways to style elements in Perspective.


### CSS Imports

Imports provide the ability to develop or author themes in a modular fashion.  They also make overriding easy (see section on overriding themes).  There are two rules that we expect you to follow when using imports.
1) Imports should be declared at the top of the each css file.
2) Each import statement must begin with the CSS at-rule `@import`, specify the relative path to the file to import, and terminate with a semicolon. Imports that do not meet this criteria will be ignored. You may use single or double quotes surrounding the import path.  For example:

        ```
         @import "../button.css";
         @import './variables.css';
        ```


## Overriding or Adapting Themes

Overriding or adapting themes is easy by leveraging the "C" in CSS (Cascading Style Sheet).  Simply add your own CSS import pointing to your own custom style sheet containing the rulesets that you want to override or adapt AFTER any existing imports.  For example, to override something declared in IA's owned light theme, add your own import in the `light.css` entry file like so:

**light.css**

```
@import "./light/index.css"
@import "./custom/overrides.css"
```

We do not attempt to rewrite this file on startup unless it does not exist.

## Creating Custom Themes

To create your own custom theme, use one of the built in themes as an example.  Any derivative themes (`light-cool`, `dark`, `dark-warm`, etc.) will serve as ideal examples for most use cases. We recommend looking at these. The derivative themes simply extend the base theme (`light`), but overrides the values of some of the CSS variables that define fundamental colors.

Create your own entry file at the root of the `themes` directory (i.e. `mytheme.css`). This is required.  Within this file you may include a combination of CSS imports, CSS rulesets, and/or variables.  The most important items to remember when authoring your own theme are:

1) An entry CSS file is required in order for your custom theme to register with Perspective.
2) Order matters. Duplicate rules that come after existing rules will override or supplement depending on declared properties between the two.
3) **The `light` theme is the base theme, and all themes should extend and override from this.** If any of the rules defined in the provided base theme (`light`) are missing from your custom theme, either from not being declared or not being imported, the result of these missing properties will be reflected in your project (for example: a button missing a border).  When creating your own custom themes, make sure that rulesets declared in the base theme (`light`) exist in your custom theme at all times, unless you have accommodated this some other way.
