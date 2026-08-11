```javascript
function formatAndCreateDashboard() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName("historique_videos");
  
  if (!dataSheet) {
    SpreadsheetApp.getUi().alert("Erreur: L'onglet 'historique_videos' n'a pas été trouvé.");
    return;
  }
  
  // ========================================================
  // 1. FORMATTAGE VISUEL DE L'HISTORIQUE
  // ========================================================
  dataSheet.setFrozenRows(1);
  
  var lastCol = dataSheet.getLastColumn();
  var headerRange = dataSheet.getRange(1, 1, 1, lastCol);
  headerRange.setFontWeight("bold");
  headerRange.setBackground("#1e293b");
  headerRange.setFontColor("#ffffff");
  headerRange.setHorizontalAlignment("center");
  headerRange.setFontFamily("Inter");
  
  var dataRange = dataSheet.getDataRange();
  
  if (dataRange.getFilter() === null) {
    dataRange.createFilter();
  }
  
  try {
    dataRange.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, true, false);
  } catch (e) {}
  
  dataSheet.autoResizeColumns(1, lastCol);

  // ========================================================
  // 2. RÉCUPÉRATION DYNAMIQUE DES COLONNES
  // ========================================================
  var headers = dataSheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var col = {};
  for (var i = 0; i < headers.length; i++) {
    col[headers[i].toString().trim()] = i;
  }
  
  // Log pour debug (visible dans le journal d'exécution Apps Script)
  Logger.log("Colonnes détectées: " + JSON.stringify(col));

  // ========================================================
  // 3. PRÉPARATION DU DASHBOARD
  // ========================================================
  var dashSheet = ss.getSheetByName("Dashboard Analytics");
  if (dashSheet) ss.deleteSheet(dashSheet);
  dashSheet = ss.insertSheet("Dashboard Analytics", 0);
  
  // Titre
  dashSheet.getRange("B2").setValue("📊 Tableau de Bord — Modern.Stories")
    .setFontSize(22).setFontWeight("bold").setFontColor("#0f172a").setFontFamily("Inter");
  dashSheet.getRange("B3").setValue("Mis à jour le " + new Date().toLocaleString("fr-FR"))
    .setFontStyle("italic").setFontColor("#94a3b8").setFontFamily("Inter");
  
  // KPIs dans une barre horizontale
  var data = dataRange.getValues();
  var totalVideos = data.length - 1;
  var totalVuesTK = 0, totalVuesYT = 0, totalVuesIG = 0;
  var totalLikesTK = 0, totalLikesYT = 0, totalLikesIG = 0;
  var totalComTK = 0, totalComYT = 0, totalComIG = 0;
  
  var categoryVues = {};
  var bgVideoVues = {};
  var voiceVues = {};
  var videoPerformance = []; // Pour le top des vidéos individuelles
  
  for (var i = 1; i < data.length; i++) {
    var vTK = col["TikTok Vues"] !== undefined ? (parseInt(data[i][col["TikTok Vues"]]) || 0) : 0;
    var vYT = col["YouTube Vues"] !== undefined ? (parseInt(data[i][col["YouTube Vues"]]) || 0) : 0;
    var vIG = col["Instagram Vues"] !== undefined ? (parseInt(data[i][col["Instagram Vues"]]) || 0) : 0;
    
    var lTK = col["TikTok Likes"] !== undefined ? (parseInt(data[i][col["TikTok Likes"]]) || 0) : 0;
    var lYT = col["YouTube Likes"] !== undefined ? (parseInt(data[i][col["YouTube Likes"]]) || 0) : 0;
    var lIG = col["Instagram Likes"] !== undefined ? (parseInt(data[i][col["Instagram Likes"]]) || 0) : 0;
    
    var cTK = col["TikTok Com"] !== undefined ? (parseInt(data[i][col["TikTok Com"]]) || 0) : 0;
    var cYT = col["YouTube Com"] !== undefined ? (parseInt(data[i][col["YouTube Com"]]) || 0) : 0;
    var cIG = col["Instagram Com"] !== undefined ? (parseInt(data[i][col["Instagram Com"]]) || 0) : 0;
    
    totalVuesTK += vTK; totalVuesYT += vYT; totalVuesIG += vIG;
    totalLikesTK += lTK; totalLikesYT += lYT; totalLikesIG += lIG;
    totalComTK += cTK; totalComYT += cYT; totalComIG += cIG;
    
    var totalVuesRow = vTK + vYT + vIG;
    
    // Catégorie
    var cat = col["Catégorie"] !== undefined ? data[i][col["Catégorie"]] : "";
    if (cat && cat !== 'Undefined' && cat !== 'N/A' && cat !== '') {
      categoryVues[cat] = (categoryVues[cat] || 0) + totalVuesRow;
    }
    
    // Vidéo de fond
    var bgVideo = col["Fichier Vidéo de Fond"] !== undefined ? data[i][col["Fichier Vidéo de Fond"]] : "";
    if (bgVideo && bgVideo !== 'Undefined' && bgVideo !== 'N/A' && bgVideo !== '') {
      bgVideo = bgVideo.toString().replace(/\.[^/.]+$/, "");
      bgVideoVues[bgVideo] = (bgVideoVues[bgVideo] || 0) + totalVuesRow;
    }
    
    // Voix
    var voice = col["Voix"] !== undefined ? data[i][col["Voix"]] : "";
    if (voice && voice !== 'Undefined' && voice !== 'N/A' && voice !== '') {
      voiceVues[voice] = (voiceVues[voice] || 0) + totalVuesRow;
    }
    
    // Top vidéos individuelles
    var titre = col["Titre Vidéo"] !== undefined ? data[i][col["Titre Vidéo"]] : ("Vidéo " + i);
    var partie = col["Partie"] !== undefined ? data[i][col["Partie"]] : "";
    var label = titre.toString().substring(0, 35) + (partie ? " (" + partie + ")" : "");
    videoPerformance.push({label: label, vues: totalVuesRow, likes: lTK + lYT + lIG, coms: cTK + cYT + cIG});
  }
  
  // Trier les vidéos par vues décroissantes et garder le top 10
  videoPerformance.sort(function(a, b) { return b.vues - a.vues; });
  var top10 = videoPerformance.slice(0, 10);
  
  // ========================================================
  // 4. KPI CARDS (ligne 5)
  // ========================================================
  var totalVues = totalVuesTK + totalVuesYT + totalVuesIG;
  var totalLikes = totalLikesTK + totalLikesYT + totalLikesIG;
  var totalCom = totalComTK + totalComYT + totalComIG;
  var engagementRate = totalVues > 0 ? ((totalLikes + totalCom) / totalVues * 100).toFixed(2) : "0.00";
  
  var kpiLabels = ["🎬 Vidéos Produites", "👁️ Vues Totales", "❤️ Likes Totaux", "💬 Commentaires", "📊 Taux d'Engagement"];
  var kpiValues = [totalVideos, totalVues, totalLikes, totalCom, engagementRate + "%"];
  var kpiColors = ["#3b82f6", "#10b981", "#ef4444", "#f59e0b", "#8b5cf6"];
  
  for (var k = 0; k < kpiLabels.length; k++) {
    var kpiCol = 2 + k * 3;
    dashSheet.getRange(5, kpiCol).setValue(kpiLabels[k]).setFontSize(10).setFontColor("#64748b").setFontWeight("bold").setFontFamily("Inter");
    dashSheet.getRange(6, kpiCol).setValue(kpiValues[k]).setFontSize(20).setFontColor(kpiColors[k]).setFontWeight("bold").setFontFamily("Inter");
    // Bordure gauche colorée
    dashSheet.getRange(5, kpiCol, 2, 1).setBorder(null, true, null, null, null, null, kpiColors[k], SpreadsheetApp.BorderStyle.SOLID_THICK);
  }

  // ========================================================
  // 5. ÉCRITURE DES DONNÉES CACHÉES POUR LES GRAPHIQUES
  // ========================================================
  // On s'assure d'avoir assez de colonnes sur le Dashboard
  var maxNeededCol = 45;
  if (dashSheet.getMaxColumns() < maxNeededCol) {
    dashSheet.insertColumnsAfter(dashSheet.getMaxColumns(), maxNeededCol - dashSheet.getMaxColumns());
  }
  
  function writeDict(sheet, startCol, title1, title2, dict) {
    sheet.getRange(1, startCol).setValue(title1);
    sheet.getRange(1, startCol + 1).setValue(title2);
    var r = 2;
    // Trier par valeur décroissante
    var sorted = Object.keys(dict).sort(function(a, b) { return dict[b] - dict[a]; });
    for (var s = 0; s < sorted.length; s++) {
      sheet.getRange(r, startCol).setValue(sorted[s]);
      sheet.getRange(r, startCol + 1).setValue(dict[sorted[s]]);
      r++;
    }
    return r;
  }
  
  var lastRowCat = writeDict(dashSheet, 28, "Catégorie", "Vues", categoryVues);   // AB, AC
  var lastRowBg = writeDict(dashSheet, 30, "Fond", "Vues", bgVideoVues);           // AD, AE
  var lastRowVoice = writeDict(dashSheet, 32, "Voix", "Vues", voiceVues);          // AF, AG
  
  // Top 10 vidéos
  dashSheet.getRange(1, 34).setValue("Vidéo");          // AH
  dashSheet.getRange(1, 35).setValue("Vues");            // AI
  dashSheet.getRange(1, 36).setValue("Likes");           // AJ
  dashSheet.getRange(1, 37).setValue("Commentaires");    // AK
  for (var t = 0; t < top10.length; t++) {
    dashSheet.getRange(t + 2, 34).setValue(top10[t].label);
    dashSheet.getRange(t + 2, 35).setValue(top10[t].vues);
    dashSheet.getRange(t + 2, 36).setValue(top10[t].likes);
    dashSheet.getRange(t + 2, 37).setValue(top10[t].coms);
  }
  var lastRowTop = top10.length + 1;
  
  // Répartition par plateforme (pour un graphique empilé)
  dashSheet.getRange(1, 39).setValue("Plateforme"); // AM
  dashSheet.getRange(1, 40).setValue("Vues");       // AN
  dashSheet.getRange(1, 41).setValue("Likes");      // AO
  dashSheet.getRange(1, 42).setValue("Commentaires"); // AP
  dashSheet.getRange(2, 39).setValue("TikTok"); dashSheet.getRange(2, 40).setValue(totalVuesTK); dashSheet.getRange(2, 41).setValue(totalLikesTK); dashSheet.getRange(2, 42).setValue(totalComTK);
  dashSheet.getRange(3, 39).setValue("YouTube"); dashSheet.getRange(3, 40).setValue(totalVuesYT); dashSheet.getRange(3, 41).setValue(totalLikesYT); dashSheet.getRange(3, 42).setValue(totalComYT);
  dashSheet.getRange(4, 39).setValue("Instagram"); dashSheet.getRange(4, 40).setValue(totalVuesIG); dashSheet.getRange(4, 41).setValue(totalLikesIG); dashSheet.getRange(4, 42).setValue(totalComIG);
  
  // ========================================================
  // 6. GRAPHIQUES
  // ========================================================
  function colLetter(idx) {
    var result = '';
    while (idx >= 0) {
      result = String.fromCharCode(65 + (idx % 26)) + result;
      idx = Math.floor(idx / 26) - 1;
    }
    return result;
  }
  
  // --- GRAPHIQUE 1 : Courbe d'évolution des vues par plateforme ---
  if (col["Date"] !== undefined) {
    var cDate = colLetter(col["Date"]);
    var chart1 = dashSheet.newChart().asLineChart()
        .addRange(dataSheet.getRange(cDate + "1:" + cDate));
    var colors1 = [];
    if (col["TikTok Vues"] !== undefined) { chart1.addRange(dataSheet.getRange(colLetter(col["TikTok Vues"]) + "1:" + colLetter(col["TikTok Vues"]))); colors1.push('#000000'); }
    if (col["YouTube Vues"] !== undefined) { chart1.addRange(dataSheet.getRange(colLetter(col["YouTube Vues"]) + "1:" + colLetter(col["YouTube Vues"]))); colors1.push('#ff0000'); }
    if (col["Instagram Vues"] !== undefined) { chart1.addRange(dataSheet.getRange(colLetter(col["Instagram Vues"]) + "1:" + colLetter(col["Instagram Vues"]))); colors1.push('#e1306c'); }
    if (colors1.length > 0) {
      chart1.setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS).setNumHeaders(1)
        .setOption('title', '📈 Évolution des vues par plateforme')
        .setOption('curveType', 'function')
        .setOption('legend', {position: 'bottom'})
        .setOption('colors', colors1)
        .setOption('width', 620).setOption('height', 370)
        .setPosition(8, 2, 0, 0);
      dashSheet.insertChart(chart1.build());
    }
  }
  
  // --- GRAPHIQUE 2 : Camembert - Répartition par Catégorie ---
  if (lastRowCat > 2) {
    var chart2 = dashSheet.newChart().asPieChart()
        .addRange(dashSheet.getRange("AB1:AC" + (lastRowCat - 1)))
        .setNumHeaders(1)
        .setOption('title', '🎯 Répartition des vues par Catégorie')
        .setOption('pieHole', 0.4)
        .setOption('legend', {position: 'right'})
        .setOption('width', 500).setOption('height', 370)
        .setPosition(8, 9, 0, 0)
        .build();
    dashSheet.insertChart(chart2);
  }
  
  // --- GRAPHIQUE 3 : Barres Horizontales - Vidéos de fond ---
  if (lastRowBg > 2) {
    var chart3 = dashSheet.newChart().asBarChart()
        .addRange(dashSheet.getRange("AD1:AE" + (lastRowBg - 1)))
        .setNumHeaders(1)
        .setOption('title', '🎬 Performances par vidéo de fond')
        .setOption('colors', ['#3b82f6'])
        .setOption('legend', {position: 'none'})
        .setOption('width', 620).setOption('height', 370)
        .setPosition(28, 2, 0, 0)
        .build();
    dashSheet.insertChart(chart3);
  }
  
  // --- GRAPHIQUE 4 : Barres - Meilleures Voix ---
  if (lastRowVoice > 2) {
    var chart4 = dashSheet.newChart().asColumnChart()
        .addRange(dashSheet.getRange("AF1:AG" + (lastRowVoice - 1)))
        .setNumHeaders(1)
        .setOption('title', '🎙️ Performances par Voix ElevenLabs')
        .setOption('colors', ['#8b5cf6'])
        .setOption('legend', {position: 'none'})
        .setOption('width', 500).setOption('height', 370)
        .setPosition(28, 9, 0, 0)
        .build();
    dashSheet.insertChart(chart4);
  }
  
  // --- GRAPHIQUE 5 : Barres empilées - Top 10 Vidéos ---
  if (lastRowTop > 2) {
    var chart5 = dashSheet.newChart().asBarChart()
        .addRange(dashSheet.getRange("AH1:AK" + lastRowTop))
        .setNumHeaders(1)
        .setOption('title', '🏆 Top 10 Vidéos (Vues + Likes + Commentaires)')
        .setOption('colors', ['#10b981', '#ef4444', '#f59e0b'])
        .setOption('isStacked', true)
        .setOption('legend', {position: 'bottom'})
        .setOption('width', 620).setOption('height', 400)
        .setPosition(48, 2, 0, 0)
        .build();
    dashSheet.insertChart(chart5);
  }
  
  // --- GRAPHIQUE 6 : Barres groupées - Comparaison Plateformes ---
  var chart6 = dashSheet.newChart().asColumnChart()
      .addRange(dashSheet.getRange("AM1:AP4"))
      .setNumHeaders(1)
      .setOption('title', '⚔️ Comparaison TikTok vs YouTube vs Instagram')
      .setOption('colors', ['#000000', '#ef4444', '#f59e0b'])
      .setOption('legend', {position: 'bottom'})
      .setOption('width', 500).setOption('height', 400)
      .setPosition(48, 9, 0, 0)
      .build();
  dashSheet.insertChart(chart6);
  
  // --- GRAPHIQUE 7 : Nuage de points - Score Reddit vs Vues ---
  if (col["Score Reddit"] !== undefined && col["TikTok Vues"] !== undefined) {
    var chart7 = dashSheet.newChart().asScatterChart()
        .addRange(dataSheet.getRange(colLetter(col["Score Reddit"]) + "1:" + colLetter(col["Score Reddit"])))
        .addRange(dataSheet.getRange(colLetter(col["TikTok Vues"]) + "1:" + colLetter(col["TikTok Vues"])))
        .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS)
        .setNumHeaders(1)
        .setOption('title', '🧪 Score Reddit → Vues TikTok ?')
        .setOption('hAxis', {title: 'Score Reddit'})
        .setOption('vAxis', {title: 'Vues TikTok'})
        .setOption('colors', ['#10b981'])
        .setOption('width', 620).setOption('height', 370)
        .setPosition(68, 2, 0, 0)
        .build();
    dashSheet.insertChart(chart7);
  }
  
  // --- GRAPHIQUE 8 : Consommation Crédits ElevenLabs ---
  if (col["Date"] !== undefined && col["Crédits Restants"] !== undefined) {
    var chart8 = dashSheet.newChart().asAreaChart()
        .addRange(dataSheet.getRange(colLetter(col["Date"]) + "1:" + colLetter(col["Date"])))
        .addRange(dataSheet.getRange(colLetter(col["Crédits Restants"]) + "1:" + colLetter(col["Crédits Restants"])))
        .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS)
        .setNumHeaders(1)
        .setOption('title', '🔋 Solde Crédits ElevenLabs')
        .setOption('colors', ['#6366f1'])
        .setOption('legend', {position: 'none'})
        .setOption('width', 500).setOption('height', 370)
        .setPosition(68, 9, 0, 0)
        .build();
    dashSheet.insertChart(chart8);
  }

  // ========================================================
  // 7. MASQUER LES COLONNES TECHNIQUES
  // ========================================================
  dashSheet.hideColumns(28, 15); // AB → AP

  // Design final
  dashSheet.setHiddenGridlines(true);
  dashSheet.setTabColor("#6366f1");
  dashSheet.setColumnWidth(1, 20); // Petite marge à gauche
  
  SpreadsheetApp.getUi().alert("✅ Dashboard Premium généré avec 8 graphiques et les KPIs !");
}
```
