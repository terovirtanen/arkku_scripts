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
        <p>Paljonko olisi sähköenergia maksanut menneinä vuosina pörssisähköä käyttäen kulutuskäyttäytymiselläni?<br>
        Sen voi laskea alla olevalla laskurilla.</p>
        <h2>Tee näin</h2>
        <p>Anna energian kulutus taulukko ja laske olisiko pörssisähkö kannattanut menneenä aikana. 
        Taulukon saa ladattua esimerkiksi Carunan verkkopalvelusta tai <a href="https://www.fingrid.fi/sahkomarkkinat/datahub/kirjautuminen-datahubin-asiakasportaaliin/" target="_blank" rel="noopener noreferrer">Fingridin datahubista</a>. Katso tarkemmin tiedoston ohjeista.<br>
        Tiedot lasketaan kuukausi- ja vuosikohtaisesti ja tulokset esitetään taulukkona ja kaaviona.</p>
        <br>

        <h2>Laske kannattaako pörssisähkö</h2>
        <br>

        <form>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <label for="energyFile" id="infoBoxTrigger">Energian kulutus taulukko:</label>
                <input type="file" id="energyFile" accept=".xlsx, .csv">
                <div class="info-icon">?</div>
                <div class="info-box">
                <p>Syötä energian kulutuksen tuntikohtainen taulukko.
                    Taulukon saa ladattua esimerkiksi Carunan verkkopalvelusta. Palvelusta saadun .xlsx taulukon voi antaa sellaisenaan josta lasketaan kulutustiedot ja kuukausihinnat pörssisähköllä. 
                    Toinen vaihtoehto on ladata taulukko FinGridin datahubista josta saa varttikohtaisen kulutustiedon .csv muodossa. Tämäkin voi ladata sellaisenaan.
                    Laskenta tehdään niillä tiedolla mitä taulukossa on, puuttuvia tietoja tai ajanjaksoja ei tarkisteta. Kuitenkin tuntikohtaista kulutusta vastaava hintatieto tulee löytyä jotta laskenta voidaan suorittaa.
                    Tiedot lasketaan yhteen kuukausi ja vuosi kohtaisesti.
                    Tiedostoja ei tallenneta mihinkään vaan selain lukee tiedoston ja tiedot lasketaan selaimessa.</p>
                    <p>Pörssisähkön tuntikohtaiset hintatiedot on haettu <a href="https://porssisahko.net/">porssisahko.net</a> sivuilta. 
                    Tuntikohtaiset hintatiedot on vuodesta 2021 alkaen ja viimeisin 16.8.2025. Tällä aikavälillä voidaan siis laskenta suorittaa.</p>
                    <p>Tuntikohtaisista tiedoista lasketaan kuukausi ja vuosikohtaiset kulutus ja hintatiedot pörssisähköllä.</p>
                    <p>
                    Hyväksytyt tiedostomuodot: .xlsx, .csv<br>
                    .xlsx :<br>
                    &nbsp;&nbsp;Taulukosta luetaan sarakkeet 'Ajankohta' ja 'Laskutettava kulutus (kWh)'. <br>
                    .csv :<br>
                    &nbsp;Tiedostossa tulee olla kaksi saraketta, päivämäärä ja kulutus kWh. Sarakkeet erotetaan puolipisteellä ja rivit rivinvaihdolla. Otsikkoriviä ei saa olla. Päivämäärä täytyy olla esimerkin mukaisessa muodossa.<br>
                    &nbsp;&nbsp;Esimerkkirivejä:<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;1.1.2024 01:00;1,05<br>
                    &nbsp;&nbsp;&nbsp;&nbsp;30.12.2024 00:00;0,4<br>
                    </p>
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
                <div class="info-icon">?</div>
                <div class="info-box">
                <p>Sähköyhtiön pörssisähköön lisättävä marginaali. Marginaali lisätään laskettuun keskihintaan ja kokonaishintaan. Muita hintaan vaikuttavia tekijöitä kuten perusmaksu ei tässä huomioida.</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <label for="priceFixed" style="width: 250px;">Kiinteä hinta c/kWh:</label>
                <input type="number" id="priceFixed" value="9.9" style="width: 60px;">
                <div class="info-icon">?</div>
                <div class="info-box">
                <p>Kiinteä hinta käytetään vertaamaan kiinteähintaista sopimusta pörssisähköön. Kiinteästä hinnasta piirretään viiva taulukkoon ja vertailuarvona taulukossa.</p>
                </div>
            </div>
            <button type="button" id="generateButton">Laske</button>
        </form>
        <h2>Kuukausi kulutus ja hinta pörssisähköllä</h2>
        <p>Optimoitu hinta on laskettu päivän suurin kulutus olisi käytetty päivän halvimpana tuntina, toiseksi suurin toiseksi halvimpana jne kunnes pienin kulutus kalleimpana tuntina.</p>
        <table id="monthlyTable"></table>
        <canvas id="monthlyChart"></canvas>
        <h2>Vuosi kulutus ja hinta pörssisähköllä</h2>
        <p>Optimoitu hinta on laskettu päivän suurin kulutus olisi käytetty päivän halvimpana tuntina, toiseksi suurin toiseksi halvimpana jne kunnes pienin kulutus kalleimpana tuntina.</p>
        <table id="yearlyTable"></table>
        <canvas id="yearlyChart"></canvas>
    </main>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.info-icon').forEach(function(icon) {
                icon.addEventListener('mouseover', function() {
                    const infoBox = icon.nextElementSibling;
                    infoBox.style.display = 'block';
                });
            });
            document.querySelectorAll('.info-box').forEach(function(icon) {
                icon.addEventListener('mouseout', function() {
                    const infoBox = icon.parentElement.querySelector('.info-box');
                    infoBox.style.display = 'none';
                });
            });
        });
    </script>
</body>
</html>