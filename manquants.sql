-- ============================================================================
-- Requête pour identifier les produits manquants/en stock faible
-- ============================================================================

-- Paramètres configurables
DECLARE @NbJours INT = 7;              -- Nombre de jours à analyser
DECLARE @StockMin INT = 0;             -- Seuil minimum de stock
DECLARE @StockMax INT = 6;             -- Seuil maximum de stock
DECLARE @DateReference DATE = CAST(GETDATE() AS DATE);  -- Date de référence (optimisation)

-- ============================================================================
-- Requête principale
-- ============================================================================

WITH ranked AS (
    -- Récupère les transactions de vente pour la période définie
    -- et classe les transactions par produit (la plus récente en premier)
    SELECT
        DESIGNATION_DETAIL,
        DATE_DOC,
        CREATED_BY,
        CODE_PRODUIT,
        ROW_NUMBER() OVER (PARTITION BY CODE_PRODUIT ORDER BY DATE_DOC DESC) AS rn
    FROM view_vte_trace
    WHERE DATE_DOC >= DATEADD(day, -@NbJours, @DateReference)
),
filtered AS (
    -- Garde uniquement la transaction la plus récente par produit
    SELECT *
    FROM ranked
    WHERE rn = 1
),
ss AS (
    -- Récupère les produits avec leur stock actuel dans l'intervalle défini
    SELECT
        p.CODE_PRODUIT,
        p.DESIGNATION_PRODUIT,
        CONVERT(VARCHAR(3), p.TYPE_PRODUIT, 2) AS TYPE_PRODUIT,
        p.IS_STOCKABLE,
        p.ACTIF,
        ISNULL(stk.QTE_STOCK, 0) AS QTE_STOCK,
        p.PSYCHOTHROPE,
        p.REFERENCE
    FROM dbo.STK_PRODUITS AS p
    LEFT JOIN (
        SELECT
            CODE_PRODUIT,
            SUM(QUANTITE) AS QTE_STOCK
        FROM dbo.STK_STOCK
        WHERE (DATE_PEREMPTION > @DateReference OR DATE_PEREMPTION IS NULL)
        GROUP BY CODE_PRODUIT
        HAVING SUM(QUANTITE) BETWEEN @StockMin AND @StockMax  -- Filtrage précoce
    ) AS stk ON stk.CODE_PRODUIT = p.CODE_PRODUIT
    WHERE stk.CODE_PRODUIT IS NOT NULL  -- Garde uniquement les produits avec stock dans l'intervalle
)
-- Résultat final : produits vendus récemment avec stock faible
SELECT
    filtered.DESIGNATION_DETAIL,
    filtered.DATE_DOC,
    filtered.CREATED_BY,
    ss.DESIGNATION_PRODUIT,
    ss.QTE_STOCK,
    ss.TYPE_PRODUIT,
    ss.REFERENCE
FROM filtered
INNER JOIN ss ON filtered.CODE_PRODUIT = ss.CODE_PRODUIT
ORDER BY ss.QTE_STOCK ASC, filtered.DATE_DOC DESC;

-- ============================================================================
-- Notes d'optimisation :
-- - @DateReference évite les appels répétés à GETDATE()
-- - Plage de dates (>=) au lieu d'égalité stricte (=) pour utiliser les index
-- - HAVING dans la sous-requête filtre avant la jointure
-- - Variables en haut facilitent les ajustements sans modifier la logique
-- ============================================================================
