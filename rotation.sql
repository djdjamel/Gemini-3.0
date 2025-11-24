-- ============================================================================
-- Analyse mensuelle des produits vendus - Version simplifiée
-- Sélectionne: CODE_PRODUIT, PRODUIT, SUM(QUANTITE_VENDU), MOIS
-- Groupé par: CODE_PRODUIT, PRODUIT, MOIS
-- ============================================================================

-- Paramètres configurables
DECLARE @EXERCICE varchar(4) = '2025';           -- Année à analyser (NULL = toutes)
DECLARE @TYPE_VENTE varchar(100) = '';           -- Types de vente (vide = tous)
DECLARE @FAMILLE_PRODUIT varchar(32) = NULL;     -- Famille de produit spécifique
DECLARE @LABO varchar(32) = NULL;                -- Laboratoire spécifique
DECLARE @TYPE_PRODUIT int = NULL;                -- Type de produit spécifique
DECLARE @REFERENCE varchar(32) = '';             -- Référence produit
DECLARE @DCI varchar(32) = '';                   -- Code DCI
DECLARE @CODE_PRODUIT varchar(32) = NULL;        -- Code produit spécifique
DECLARE @MOIS varchar(100) = '';                 -- Mois spécifiques (ex: '1,2,3' pour Jan-Mar)
DECLARE @SPECIALITE varchar(32) = NULL;          -- Spécialité
DECLARE @TAG_PRODUIT varchar(max) = '';          -- Tags produit
DECLARE @TAG_STOCK varchar(max) = '';            -- Tags stock

-- ============================================================================
-- Requête principale
-- ============================================================================

SELECT
    av.CODE_PRODUIT,
    av.PRODUIT,
    SUM(av.QUANTITE_VENDU) AS QUANTITE_VENDU,
    av.MOIS
FROM (
    -- VENTE comptoir / retour comptoir (pas en saisie) && VENTE CVM / bon de livraison / bon de retour
    SELECT
        VTE_D.CODE_PRODUIT,
        stkp.DESIGNATION_PRODUIT AS PRODUIT,
        dbo.Get_Month_Name(MONTH(VTE.DATE_VENTE), 1) AS MOIS,
        (VTE_D.QUANTITE * VTE.SENS_DOC) AS QUANTITE_VENDU,
        VTE.TYPE_VENTE,
        VTE_D.ID_STOCK
    FROM dbo.VTE_VENTE_DETAIL VTE_D
    INNER JOIN VTE_VENTE VTE ON VTE.CODE_VENTE = VTE_D.CODE_VENTE
    INNER JOIN STK_PRODUITS STKP ON STKP.CODE_PRODUIT = VTE_D.CODE_PRODUIT
    LEFT JOIN dbo.BSE_PRODUIT_LABO LAB ON LAB.CODE = STKP.CODE_LABO
    LEFT JOIN BSE_PRODUIT_FAMILLE F ON F.CODE = STKP.CODE_FAMILLE
    WHERE
        (
            (VTE.TYPE_VENTE IN ('VC', 'RC') AND TYPE_VALIDATION <> 0)
            OR
            (VTE.TYPE_VENTE IN ('VM', 'BL', 'BR'))
        )
        AND (YEAR(VTE.DATE_VENTE) = @EXERCICE OR ISNULL(@EXERCICE, '') = '')
        AND (STKP.TYPE_PRODUIT = @TYPE_PRODUIT OR ISNULL(@TYPE_PRODUIT, 0) = 0)
        AND (F.DESIGNATION = @FAMILLE_PRODUIT OR ISNULL(@FAMILLE_PRODUIT, '') = '')
        AND (LAB.CODE = @LABO OR ISNULL(@LABO, '') = '')
        AND (STKP.REFERENCE = @REFERENCE OR ISNULL(@REFERENCE, '') = '')
        AND (STKP.CODE_DCI = @DCI OR ISNULL(@DCI, '') = '')
        AND (STKP.CODE_PRODUIT = @CODE_PRODUIT OR ISNULL(@CODE_PRODUIT, '') = '')
        AND (MONTH(VTE.DATE_VENTE) IN (SELECT * FROM SplitString(@MOIS)) OR ISNULL(@MOIS, '') = '')
        AND (STKP.SPECIALITE = @SPECIALITE OR ISNULL(@SPECIALITE, '') = '')

    UNION ALL

    -- VENTE instance CHIFA
    SELECT
        VTE_D.CODE_PRODUIT,
        stkp.DESIGNATION_PRODUIT AS PRODUIT,
        dbo.Get_Month_Name(MONTH(VTE.DATE_VENTE), 1) AS MOIS,
        ((VTE_D.QUANTITE - ISNULL(di.QTE_ARCHIVE, 0)) * VTE.SENS_DOC) AS QUANTITE_VENDU,
        VTE.TYPE_VENTE,
        VTE_D.ID_STOCK
    FROM dbo.VTE_VENTE_DETAIL VTE_D
    INNER JOIN VTE_VENTE VTE ON VTE.CODE_VENTE = VTE_D.CODE_VENTE
    INNER JOIN STK_PRODUITS STKP ON STKP.CODE_PRODUIT = VTE_D.CODE_PRODUIT
    LEFT JOIN dbo.BSE_PRODUIT_LABO LAB ON LAB.CODE = STKP.CODE_LABO
    LEFT JOIN BSE_PRODUIT_FAMILLE F ON F.CODE = STKP.CODE_FAMILLE
    LEFT JOIN View_VTE_INSTANCE_DETAIL di ON VTE_D.CODE_DETAIL = di.CODE_DETAIL
    WHERE
        (
            VTE.TYPE_VENTE IN ('VI')
            AND VTE.ETAT_VENTE <> 'A'
            AND (VTE_D.QUANTITE - ISNULL(di.QTE_ARCHIVE, 0)) > 0
        )
        AND (YEAR(VTE.DATE_VENTE) = @EXERCICE OR ISNULL(@EXERCICE, '') = '')
        AND (STKP.TYPE_PRODUIT = @TYPE_PRODUIT OR ISNULL(@TYPE_PRODUIT, 0) = 0)
        AND (F.DESIGNATION = @FAMILLE_PRODUIT OR ISNULL(@FAMILLE_PRODUIT, '') = '')
        AND (LAB.CODE = @LABO OR ISNULL(@LABO, '') = '')
        AND (STKP.REFERENCE = @REFERENCE OR ISNULL(@REFERENCE, '') = '')
        AND (STKP.CODE_DCI = @DCI OR ISNULL(@DCI, '') = '')
        AND (STKP.CODE_PRODUIT = @CODE_PRODUIT OR ISNULL(@CODE_PRODUIT, '') = '')
        AND (MONTH(VTE.DATE_VENTE) IN (SELECT * FROM SplitString(@MOIS)) OR ISNULL(@MOIS, '') = '')
        AND (STKP.SPECIALITE = @SPECIALITE OR ISNULL(@SPECIALITE, '') = '')

    UNION ALL

    -- VENTE facture de vente non associée au bon de livraison
    SELECT
        VTE_D.CODE_PRODUIT,
        stkp.DESIGNATION_PRODUIT AS PRODUIT,
        dbo.Get_Month_Name(MONTH(VTE.DATE_VENTE), 1) AS MOIS,
        (VTE_D.QUANTITE * VTE.SENS_DOC) AS QUANTITE_VENDU,
        VTE.TYPE_VENTE,
        VTE_D.ID_STOCK
    FROM dbo.VTE_VENTE_DETAIL VTE_D
    INNER JOIN VTE_VENTE VTE ON VTE.CODE_VENTE = VTE_D.CODE_VENTE
    INNER JOIN STK_PRODUITS STKP ON STKP.CODE_PRODUIT = VTE_D.CODE_PRODUIT
    LEFT JOIN dbo.BSE_PRODUIT_LABO LAB ON LAB.CODE = STKP.CODE_LABO
    LEFT JOIN BSE_PRODUIT_FAMILLE F ON F.CODE = STKP.CODE_FAMILLE
    WHERE
        (
            VTE.TYPE_VENTE = 'FV'
            AND ISNULL(CODE_ORIGINE, '') NOT IN (SELECT CODE_VENTE FROM VTE_VENTE WHERE TYPE_VENTE = 'BL')
        )
        AND (YEAR(VTE.DATE_VENTE) = @EXERCICE OR ISNULL(@EXERCICE, '') = '')
        AND (STKP.TYPE_PRODUIT = @TYPE_PRODUIT OR ISNULL(@TYPE_PRODUIT, 0) = 0)
        AND (F.DESIGNATION = @FAMILLE_PRODUIT OR ISNULL(@FAMILLE_PRODUIT, '') = '')
        AND (LAB.CODE = @LABO OR ISNULL(@LABO, '') = '')
        AND (STKP.REFERENCE = @REFERENCE OR ISNULL(@REFERENCE, '') = '')
        AND (STKP.CODE_DCI = @DCI OR ISNULL(@DCI, '') = '')
        AND (STKP.CODE_PRODUIT = @CODE_PRODUIT OR ISNULL(@CODE_PRODUIT, '') = '')
        AND (MONTH(VTE.DATE_VENTE) IN (SELECT * FROM SplitString(@MOIS)) OR ISNULL(@MOIS, '') = '')
        AND (STKP.SPECIALITE = @SPECIALITE OR ISNULL(@SPECIALITE, '') = '')

    UNION ALL

    -- PHARMNOS - CASNOS
    SELECT
        FCS_D.CODE_PRODUIT,
        stkp.DESIGNATION_PRODUIT AS PRODUIT,
        dbo.Get_Month_Name(MONTH(FCS.DATE_FACTURE), 1) AS MOIS,
        FCS_D.QUANTITE AS QUANTITE_VENDU,
        'FPN' AS TYPE_VENTE,
        FCS_D.ID_STOCK
    FROM dbo.DETAIL_FACTURE_CASNOS FCS_D
    INNER JOIN dbo.FACTURE_CASNOS FCS ON FCS.NUM_FACTURE = FCS_D.NUM_FACTURE
    INNER JOIN STK_PRODUITS STKP ON STKP.CODE_PRODUIT = FCS_D.CODE_PRODUIT
    LEFT JOIN dbo.BSE_PRODUIT_LABO LAB ON LAB.CODE = STKP.CODE_LABO
    LEFT JOIN BSE_PRODUIT_FAMILLE F ON F.CODE = STKP.CODE_FAMILLE
    WHERE
        (YEAR(FCS.DATE_FACTURE) = @EXERCICE OR ISNULL(@EXERCICE, '') = '')
        AND (STKP.TYPE_PRODUIT = @TYPE_PRODUIT OR ISNULL(@TYPE_PRODUIT, 0) = 0)
        AND (F.DESIGNATION = @FAMILLE_PRODUIT OR ISNULL(@FAMILLE_PRODUIT, '') = '')
        AND (LAB.CODE = @LABO OR ISNULL(@LABO, '') = '')
        AND (STKP.REFERENCE = @REFERENCE OR ISNULL(@REFERENCE, '') = '')
        AND (STKP.CODE_DCI = @DCI OR ISNULL(@DCI, '') = '')
        AND (STKP.CODE_PRODUIT = @CODE_PRODUIT OR ISNULL(@CODE_PRODUIT, '') = '')
        AND (MONTH(FCS.DATE_FACTURE) IN (SELECT * FROM SplitString(@MOIS)) OR ISNULL(@MOIS, '') = '')
        AND (STKP.SPECIALITE = @SPECIALITE OR ISNULL(@SPECIALITE, '') = '')

    UNION ALL

    -- CHIFA - CNAS / CASNOS / HORS CHIFA
    SELECT
        FCH_D.CODE_PRODUIT,
        stkp.DESIGNATION_PRODUIT AS PRODUIT,
        dbo.Get_Month_Name(MONTH(FCH.DATE_FACTURE), 1) AS MOIS,
        FCH_D.QUANTITE AS QUANTITE_VENDU,
        CASE SUBSTRING(FCH.CENTRE, 1, 1)
            WHEN '1' THEN 'FCN'
            WHEN '2' THEN 'FCS'
            WHEN '9' THEN 'FHC'
        END AS TYPE_VENTE,
        FCH_D.ID_STOCK
    FROM dbo.DETAIL_FACTURE_CHIFA FCH_D
    INNER JOIN dbo.FACTURE_CHIFA FCH ON FCH.NUM_FACTURE = FCH_D.NUM_FACTURE
    INNER JOIN STK_PRODUITS STKP ON STKP.CODE_PRODUIT = FCH_D.CODE_PRODUIT
    LEFT JOIN dbo.BSE_PRODUIT_LABO LAB ON LAB.CODE = STKP.CODE_LABO
    LEFT JOIN BSE_PRODUIT_FAMILLE F ON F.CODE = STKP.CODE_FAMILLE
    WHERE
        (YEAR(FCH.DATE_FACTURE) = @EXERCICE OR ISNULL(@EXERCICE, '') = '')
        AND (STKP.TYPE_PRODUIT = @TYPE_PRODUIT OR ISNULL(@TYPE_PRODUIT, 0) = 0)
        AND (F.DESIGNATION = @FAMILLE_PRODUIT OR ISNULL(@FAMILLE_PRODUIT, '') = '')
        AND (LAB.CODE = @LABO OR ISNULL(@LABO, '') = '')
        AND (STKP.REFERENCE = @REFERENCE OR ISNULL(@REFERENCE, '') = '')
        AND (STKP.CODE_DCI = @DCI OR ISNULL(@DCI, '') = '')
        AND (STKP.CODE_PRODUIT = @CODE_PRODUIT OR ISNULL(@CODE_PRODUIT, '') = '')
        AND (MONTH(FCH.DATE_FACTURE) IN (SELECT * FROM SplitString(@MOIS)) OR ISNULL(@MOIS, '') = '')
        AND (STKP.SPECIALITE = @SPECIALITE OR ISNULL(@SPECIALITE, '') = '')
) av
WHERE (
    (CHARINDEX(ISNULL(RTRIM(av.TYPE_VENTE), ''), @TYPE_VENTE) <> 0)
    OR ISNULL(@TYPE_VENTE, '') = ''
)
AND (
    (av.CODE_PRODUIT IN (SELECT CODE_PRODUIT FROM STK_PRODUIT_TAG WHERE CODE_TAG IN (SELECT * FROM SplitString(@TAG_PRODUIT)) GROUP BY CODE_PRODUIT))
    OR ISNULL(@TAG_PRODUIT, '') = ''
)
AND (
    (av.ID_STOCK IN (SELECT ID_STOCK FROM STK_STOCK_MOTIVATION WHERE CODE_TAG IN (SELECT * FROM SplitString(@TAG_STOCK)) GROUP BY ID_STOCK))
    OR ISNULL(@TAG_STOCK, '') = ''
)
GROUP BY av.CODE_PRODUIT, av.PRODUIT, av.MOIS
ORDER BY av.CODE_PRODUIT, av.MOIS;

-- ============================================================================
-- Notes :
-- - Cette requête agrège toutes les ventes (comptoir, CVM, factures, etc.)
-- - Les quantités sont déjà multipliées par SENS_DOC (pour gérer les retours)
-- - Modifiez les paramètres en haut pour filtrer les résultats
-- ============================================================================
