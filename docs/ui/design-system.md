# KLASS Design System — v2.0

> Phase 3.5 — Documentation du système de design unifié

---

## Philosophie

KLASS utilise un design system cohérent inspiré du Figma fourni. Le principe directeur est : **rigueur et clarté dans la densité de l'information**. Chaque écran doit répondre à une question métier précise sans surcharge visuelle.

---

## Variables CSS

Toutes les couleurs et espacements sont définis dans `static/css/klass.css` :

```css
--klass-primary:      #4361EE   /* Bleu principal */
--klass-primary-dark: #3451d1
--klass-sidebar-bg:   #1E2140   /* Bleu nuit (sidebar) */
--klass-bg:           #F4F6F9   /* Fond de page */
--klass-card-bg:      #FFFFFF
--klass-border:       #E8EDF5

--klass-green:   #22C55E
--klass-red:     #EF4444
--klass-yellow:  #F59E0B
--klass-purple:  #8B5CF6
--klass-teal:    #14B8A6
--klass-orange:  #F97316
```

---

## Layout

### Structure de page (utilisateur authentifié)
```
Navbar fixe (60px)
├── Sidebar gauche (240px, dark navy)
│   ├── Logo + nom école
│   ├── Navigation sections
│   └── User card (logout)
└── Main (#klass-main, flex-grow)
    ├── Messages flash
    └── {% block content %}
```

**Mobile (< 992px)** : La sidebar est masquée. Le bouton hamburger `#sidebar-toggler` la fait glisser depuis la gauche comme un drawer, avec un overlay sombre.

---

## Composants

### Page Header
```html
<div class="page-header">
  <div class="page-header-left">
    <h1 class="page-header-title">Titre</h1>
    <p class="page-header-sub">Sous-titre</p>
  </div>
  <div class="page-header-actions">
    <a href="..." class="btn btn-primary">Action</a>
  </div>
</div>
```

### Breadcrumb
```html
<div class="klass-breadcrumb">
  <a href="...">Section</a>
  <i class="bi bi-chevron-right klass-breadcrumb-sep"></i>
  <span class="klass-breadcrumb-current">Page actuelle</span>
</div>
```

### Stat Cards
```html
<div class="card">
  <div class="stat-card">
    <div class="stat-card-icon blue">  <!-- blue|green|yellow|red|purple|teal|orange -->
      <i class="bi bi-people-fill"></i>
    </div>
    <div>
      <div class="stat-card-count">42</div>
      <div class="stat-card-label">Élèves actifs</div>
    </div>
  </div>
</div>
```

### Empty State
```html
<div class="empty-state">
  <div class="empty-state-icon"><i class="bi bi-people"></i></div>
  <h5 class="empty-state-title">Aucun élève enregistré</h5>
  <p class="empty-state-desc">Commencez par ajouter le premier élève.</p>
  <a href="..." class="btn btn-primary" style="border-radius:10px;">
    <i class="bi bi-plus-lg me-1"></i>Ajouter
  </a>
</div>
```

### Info Item (pages détail)
```html
<div class="info-item">
  <div class="info-label">Date de naissance</div>
  <div class="info-value">15/03/2010</div>
</div>
```

### Table Standard
```html
<table class="table table-hover mb-0 align-middle">
  <thead>
    <tr style="background:#FAFBFD;">
      <th style="padding:.9rem 1.25rem;font-size:.75rem;font-weight:600;text-transform:uppercase;
                 letter-spacing:.05em;color:var(--klass-text-muted);">COLONNE</th>
    </tr>
  </thead>
  <tbody>...</tbody>
</table>
```

### Row Avatar
```html
<span class="row-avatar">AB</span>                  <!-- bleu par défaut -->
<span class="row-avatar green">CD</span>            <!-- vert -->
<span class="row-avatar purple">EF</span>           <!-- violet -->
```

### Badges de statut
| Statut    | Classes Bootstrap                          |
|-----------|--------------------------------------------|
| active    | `badge bg-success-subtle text-success`     |
| inactive  | `badge bg-secondary-subtle text-secondary` |
| pending   | `badge bg-warning-subtle text-warning`     |
| cancelled | `badge bg-danger-subtle text-danger`       |
| completed | `badge bg-info-subtle text-info`           |
| archived  | `badge bg-dark-subtle text-secondary`      |

### Anti double-submit (formulaires)
Ajouter `data-submit-once` sur le `<form>`. Le JS intercepte la soumission, désactive le bouton et affiche un spinner.

```html
<form method="post" novalidate data-submit-once>
  ...
  <button type="submit" class="btn btn-primary">Enregistrer</button>
</form>
```

### Filter Bar
```html
<div class="filter-bar">
  <form method="get" class="row g-2 align-items-end">
    ...
  </form>
</div>
```

### Wizard Steps
```html
<div class="wizard-steps">
  <div class="wizard-step done">
    <div class="wizard-step-circle"><i class="bi bi-check2"></i></div>
    <div class="wizard-step-label">Étape 1</div>
  </div>
  <div class="wizard-step-connector done"></div>
  <div class="wizard-step active">
    <div class="wizard-step-circle">2</div>
    <div class="wizard-step-label">Étape 2</div>
  </div>
</div>
```

---

## Typographie

- **Famille** : Inter (Google Fonts), fallback system-ui
- **Tailles** :
  - Titre de page : `1.35rem / fw-bold`
  - Corps : `0.875rem`
  - Petit texte / labels : `0.78–0.82rem`
  - Table headers : `0.75rem / uppercase`
  - Badges : `0.75rem`

---

## Grille responsive

- `< 576px` : padding réduit, cartes empilées, table scrollable
- `576–991px` : sidebar cachée + hamburger
- `≥ 992px` : sidebar fixe 240px, contenu fluide

---

## Icons

Bootstrap Icons 1.11.3 (`bi bi-*`). Principales icônes utilisées :

| Usage         | Icône                         |
|---------------|-------------------------------|
| Élèves        | `bi-people-fill`              |
| Enseignants   | `bi-person-badge-fill`        |
| Classes       | `bi-door-open`                |
| Années        | `bi-calendar-check`           |
| Niveaux       | `bi-bookmark-fill`            |
| Options       | `bi-diagram-2-fill`           |
| Salles        | `bi-building`                 |
| Inscriptions  | `bi-journal-text`             |
| Parents       | `bi-person-hearts`            |
| Paramètres    | `bi-gear`                     |
| Tableau bord  | `bi-speedometer2`             |
