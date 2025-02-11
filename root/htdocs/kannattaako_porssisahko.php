<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kannattaako Pörssisähkö</title>
    <link rel="stylesheet" href="kannattaako_porssisahko.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.16.9/xlsx.full.min.js"></script>
    <script>
        const priceFileContent = `<?php echo file_get_contents('./sahkon-hinta-latest.csv'); ?>`;
    </script>
    <script src="kannattaako_porssisahko.js" defer></script>
</head>
<body>
    <h1>Kannattaako pörssisähkö</h1>
    <form>
        <label for="energyFile">Energian kulutus taulukko:</label>
        <input type="file" id="energyFile" accept=".xlsx, .csv"><br><br>
        <label for="priceMargin">Pörssisähkösopimuksen marginaali c/kWh:</label>
        <input type="number" id="priceMargin" value="0.5"><br><br>
        <label for="priceFixed">Kiinteä hinta c/kWh:</label>
        <input type="number" id="priceFixed" value="9.9"><br><br>
        <button type="button" id="generateButton">Laske</button>
    </form>
    <h2>Kuukausi kulutus</h2>
    <table id="monthlyTable"></table>
    <canvas id="monthlyChart"></canvas>
    <h2>Vuosi kulutus</h2>
    <table id="yearlyTable"></table>
    <canvas id="yearlyChart"></canvas>
</body>
</html>