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
    <main>
        <h1>Kannattaako pörssisähkö</h1>
        <h2>Tee näin</h2>
        <p>Syötä energian kulutus taulukko ja laske kannattaako pörssisähkö.
            Taulukon saa ladattua esimerkiksi Carunan verkkopalvelusta. Palvelusta saadun .xlsx taulukon voi antaa sellaisenaan josta lasketaan kulutustiedot ja kuukausihinnat pörssisähköllä. 
            Laskenta tehdään niillä tiedolla mitä taulukossa on, puuttuvia tietoja tai ajanjaksoja ei tarkisteta. Kuitenkin tuntikohtaista kulutusta vastaava hintatieto tulee löytyä jotta laskenta voidaan suorittaa.
            Tiedot lasketaan yhteen kuukausi ja vuosi kohtaisesti.
            Voit myös antaa .csv tiedoston jossa on kahdessa sarakkeessa päivämäärä ja kulutus kWh. Tiedostossa tulee olla päivämäärä ja kulutus erotettuna puolipisteellä ja rivit rivinvaihdolla. 
            Tiedostoja ei tallenneta mihinkään vaan selain lukee tiedoston ja tiedot lasketaan selaimessa.</p>
        <p>Pörssisähkön tuntikohtaiset hintatiedot on haettu <a href="https://porssisahko.net/">porssisahko.net</a> sivuilta. 
            Tuntikohtaiset hintatiedot on vuodesta 2021 alkaen ja viimeisin 31.1.2025. Tällä aikavälillä voidaan siis laskenta suorittaa.</p>
        <p>Sähköyhtiön pörssisähköön lisättävä marginaali voidaan asettaa. Marginaali lisätään laskettuun keskihintaan ja kokonaishintaan. Muita hintaan vaikuttavia tekijöitä kuten perusmaksu ei tässä huomioida.</p>
        <p>Kiinteä hinta käytetään vertaamaan kiinteähintaista sopimusta pörssisähköön. Kiinteästä hinnasta piirretään viiva taulukkoon, sitä ei käytetä laskennassa.</p>
        <p>Tuntikohtaisista tiedoista lasketaan kuukausi ja vuosikohtaiset kulutus ja hintatiedot pörssisähköllä. Tiedot esitetään taulukossa ja kaaviossa.</p>
        <br>

        <h2>Laske kannattaako pörssisähkö</h2>
        <br>

        <form>
            <label for="energyFile" id="infoBoxTrigger">Energian kulutus taulukko:</label>
            <input type="file" id="energyFile" accept=".xlsx, .csv"><br><br>
            <div style="margin-bottom: 10px; font-size: 0.9em; color: #555; position: relative;">
                <div id="infoBox" style="display: none; position: absolute; top: 20px; left: 0; background-color: #f9f9f9; border: 1px solid #ccc; padding: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                Hyväksytyt tiedostomuodot: .xlsx, .csv<br>
                .xlsx :<br>
                &nbsp;&nbsp;Taulukosta luetaan sarakkeet 'Ajankohta' ja 'Laskutettava kulutus (kWh)'. <br>
                .csv :<br>
                &nbsp;Tiedostossa tulee olla kaksi saraketta, päivämäärä ja kulutus kWh. Sarakkeet erotetaan puolipisteellä ja rivit rivinvaihdolla.<br>
                &nbsp;&nbsp;Esimerkkirivejä:<br>
                &nbsp;&nbsp;&nbsp;&nbsp;1.1.2024 01:00;1,05<br>
                &nbsp;&nbsp;&nbsp;&nbsp;30.12.2024 00:00;0,4<br>
                </div>
            </div>
            <script>
                document.getElementById('infoBoxTrigger').addEventListener('mouseover', function() {
                document.getElementById('infoBox').style.display = 'block';
                });
                document.getElementById('infoBoxTrigger').addEventListener('mouseout', function() {
                document.getElementById('infoBox').style.display = 'none';
                });
            </script>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <label for="priceMargin" style="width: 250px;">Pörssisähkösopimuksen marginaali c/kWh:</label>
                <input type="number" id="priceMargin" value="0.5" style="width: 60px;">
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <label for="priceFixed" style="width: 250px;">Kiinteä hinta c/kWh:</label>
                <input type="number" id="priceFixed" value="9.9" style="width: 60px;">
            </div>
            <button type="button" id="generateButton">Laske</button>
        </form>
        <h2>Kuukausi kulutus ja hinta pörssisähköllä</h2>
        <table id="monthlyTable"></table>
        <canvas id="monthlyChart"></canvas>
        <h2>Vuosi kulutus ja hinta pörssisähköllä</h2>
        <table id="yearlyTable"></table>
        <canvas id="yearlyChart"></canvas>
    </main>
</body>
</html>