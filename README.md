# LeLitParfait.fr — Comparatif Matelas & Literie

## Structure du projet

```
lelitparfait/
├── index.html                              ← Page principale (comparatif, guide, FAQ)
├── mentions-legales.html                   ← Mentions légales (obligatoire)
├── politique-confidentialite.html          ← Politique RGPD (obligatoire)
├── blog/
│   ├── mousse-vs-ressorts.html            ← Article : mousse vs ressorts
│   ├── meilleurs-oreillers-cervicales.html ← Article : oreillers cervicales
│   └── mal-de-dos-matelas.html            ← Article : mal de dos et matelas
├── img/                                    ← Images produits (à remplir)
└── README.md                               ← Ce fichier
```

## Déploiement sur GitHub Pages

### 1. Créer le repository
- Aller sur github.com → New repository
- Nom : `lelitparfait`
- Public → Create repository

### 2. Uploader les fichiers
- Cliquer "uploading an existing file"
- Glisser-déposer TOUS les fichiers et dossiers
- Commit changes

### 3. Activer GitHub Pages
- Settings → Pages
- Source : Deploy from a branch
- Branch : main / root
- Save

### 4. Configurer le domaine (Infomaniak)
Dans la zone DNS de lelitparfait.fr chez Infomaniak, ajouter :

| Type  | Hôte | Valeur                    |
|-------|------|---------------------------|
| A     | @    | 185.199.108.153           |
| A     | @    | 185.199.109.153           |
| A     | @    | 185.199.110.153           |
| A     | @    | 185.199.111.153           |
| CNAME | www  | VOTRE-PSEUDO.github.io    |

### 5. Connecter dans GitHub
- Settings → Pages → Custom domain : `lelitparfait.fr`
- Cocher "Enforce HTTPS"

## Personnalisation obligatoire avant mise en ligne

### Remplacer le tag Amazon
Rechercher `VOTRE-TAG-21` dans TOUS les fichiers et remplacer par votre vrai tag Amazon Partenaires (format : `monsite-21`).

Pour obtenir votre tag :
1. S'inscrire sur https://partenaires.amazon.fr
2. Le tag sera de la forme `lelitparfait-21` ou similaire

### Compléter les mentions légales
Dans `mentions-legales.html` et `politique-confidentialite.html`, remplacer :
- `[PRÉNOM NOM DE VOTRE COMPAGNE]` → nom complet
- `[À COMPLÉTER]` pour le SIREN
- `[ADRESSE À COMPLÉTER]` → adresse professionnelle
- `[EMAIL À COMPLÉTER]` → email de contact

### Compléter le footer de index.html
Dans `index.html`, section footer-legal, remplacer :
- `[À COMPLÉTER]` pour le SIREN
- `[NOM PRÉNOM À COMPLÉTER]` → nom de l'éditrice

### Mettre à jour les URLs canoniques
Si votre domaine final n'est pas `lelitparfait.fr`, remplacer toutes les occurrences dans les fichiers.

## Programme d'affiliation Amazon

### Inscription
1. Aller sur https://partenaires.amazon.fr
2. S'inscrire avec le compte Amazon de l'auto-entrepreneuse
3. Renseigner l'URL du site : https://lelitparfait.fr
4. Récupérer le tag Associates

### Remplacer les liens
Utiliser Ctrl+Shift+H dans VSCode pour remplacer `VOTRE-TAG-21` par le vrai tag dans tous les fichiers.

### API Product Advertising (optionnel, plus tard)
L'accès à l'API PA v5 nécessite au moins 3 ventes qualifiées dans les 30 derniers jours. En attendant, les liens de recherche Amazon (`/s?k=...&tag=...`) fonctionnent parfaitement.

## Google Search Console

1. Aller sur https://search.google.com/search-console
2. Ajouter la propriété `lelitparfait.fr`
3. Vérifier via DNS (ajouter un enregistrement TXT chez Infomaniak)
4. Soumettre le sitemap (créer un sitemap.xml simple ou laisser Google crawler)

## Maintenance

- **Prix** : vérifier les prix Amazon chaque trimestre
- **dateModified** : mettre à jour dans le schema.org de index.html à chaque révision
- **Contenu** : ajouter de nouveaux articles de blog régulièrement pour renforcer le SEO
