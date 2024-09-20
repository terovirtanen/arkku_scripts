<!DOCTYPE html>
<html>
<head>
    <title>Solar field power</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <script>
        function addNewFields() {
            // Create a new div to hold the new set of input fields
            var newDiv = document.createElement('div');
            newDiv.className = 'input-set';

            // Create the new input fields
            newDiv.innerHTML = `
                <label for="tiltAngle">Tilt angle:</label>
                <input type="number" name="tiltAngle[]" step="0.1" required>
                <br>
                <label for="panelAzimuth">Panel Azimuth:</label>
                <input type="number" name="panelAzimuth[]" step="0.1" required>
                <br>
                <label for="peakPower">Peak Power (Wh):</label>
                <input type="number" name="peakPower[]" step="0.1" required>
                <br>
                <label for="panelEfficiency">Panel Efficiency:</label>
                <input type="number" name="panelEfficiency[]" step="0.01" required value="1.00">
                <br><br>
            `;

            // Append the new div to the form
            document.getElementById('inputFields').appendChild(newDiv);
        }
    </script>
</head>
<body>

<h1>Solar field power</h1>

<form method="post" action="">
    <label for="longitude">Longitude:</label>
    <input type="number" id="longitude" name="longitude" step="0.0001" required value="<?php echo isset($_POST['longitude']) ? htmlspecialchars($_POST['longitude']) : ''; ?>">
    <br><br>
    <label for="latitude">Latitude:</label>
    <input type="number" id="latitude" name="latitude" step="0.0001" required value="<?php echo isset($_POST['latitude']) ? htmlspecialchars($_POST['latitude']) : ''; ?>">
    <br><br>
    <div id="inputFields">
        <?php
        if ($_SERVER["REQUEST_METHOD"] == "POST") {
            $tiltAngles = $_POST['tiltAngle'];
            $panelAzimuths = $_POST['panelAzimuth'];
            $peakPowers = $_POST['peakPower'];
            $panelEfficiencies = $_POST['panelEfficiency'];

            foreach ($tiltAngles as $index => $tiltAngle) {
                $tiltAngleValue = htmlspecialchars($tiltAngle);
                $panelAzimuthValue = htmlspecialchars($panelAzimuths[$index]);
                $peakPowerValue = htmlspecialchars($peakPowers[$index]);
                $panelEfficiencyValue = htmlspecialchars($panelEfficiencies[$index]);
                echo "
                <div class='input-set'>
                    <label for='tiltAngle'>Tilt angle:</label>
                    <input type='number' name='tiltAngle[]' step='0.1' required value='$tiltAngleValue'>
                    <br>
                    <label for='panelAzimuth'>Panel Azimuth:</label>
                    <input type='number' name='panelAzimuth[]' step='0.1' required value='$panelAzimuthValue'>
                    <br>
                    <label for='peakPower'>Peak Power (Wh):</label>
                    <input type='number' name='peakPower[]' step='0.1' required value='$peakPowerValue'>
                    <br>
                    <label for='panelEfficiency'>Panel Efficiency:</label>
                    <input type='number' name='panelEfficiency[]' step='0.01' required value='$panelEfficiencyValue'>
                    <br><br>
                </div>";
            }
        } else {
            echo "
            <div class='input-set'>
                <label for='tiltAngle'>Tilt angle:</label>
                <input type='number' name='tiltAngle[]' step='0.1' required>
                <br>
                <label for='panelAzimuth'>Panel Azimuth:</label>
                <input type='number' name='panelAzimuth[]' step='0.1' required>
                <br>
                <label for='peakPower'>Peak Power (Wh):</label>
                <input type='number' name='peakPower[]' step='0.1' required>
                <br>
                <label for='panelEfficiency'>Panel Efficiency:</label>
                <input type='number' name='panelEfficiency[]' step='0.01' required value='1.00'>
                <br><br>
            </div>";
        }
        ?>
    </div>
    <input type="button" value="New" onclick="addNewFields()">
    <input type="submit" value="Submit">
</form>

<?php

include_once '../SolarPower.php';

$solarField = new SolarFieldPower();

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Read the values from the form submission
    $longitude = floatval($_POST['longitude']);
    $latitude = floatval($_POST['latitude']);
    $tiltAngles = $_POST['tiltAngle'];
    $panelAzimuths = $_POST['panelAzimuth'];
    $peakPowers = $_POST['peakPower'];
    $panelEfficiencies = $_POST['panelEfficiency'];

    echo "Longitude: " . htmlspecialchars($longitude) . "<br>";
    echo "Latitude: " . htmlspecialchars($latitude) . "<br><br>";

    $solarField->SetLocation(floatval($latitude), floatval($longitude));

    foreach ($tiltAngles as $index => $tiltAngle) {
        $tiltAngle = floatval($tiltAngle);
        $panelAzimuth = floatval($panelAzimuths[$index]);
        $peakPower = floatval($peakPowers[$index]);
        $panelEfficiency = floatval($panelEfficiencies[$index]);

        echo "Tilt angle: " . htmlspecialchars($tiltAngle) . " degrees<br>";
        echo "Panel Azimuth: " . htmlspecialchars($panelAzimuth) . " degrees<br>";
        echo "Peak Power: " . htmlspecialchars($peakPower) . " Wh<br>";
        echo "Panel Efficiency: " . htmlspecialchars($panelEfficiency) . "<br><br>";

        $solarField->AddPanel($tiltAngle, $panelAzimuth, $peakPower);

    }

    echo "Calculate power for this year<br>";

    // Get the current year
    $year = date("Y");
    
    // Initialize an array to store monthly power data
    $monthlyPowers = [];

    // Loop through each month of the year
    for ($month = 1; $month <= 12; $month++) {
        // Get the number of days in the current month
        $daysInMonth = cal_days_in_month(CAL_GREGORIAN, $month, $year);
        $monthlyPower = 0;

        // Loop through each day of the month
        for ($day = 1; $day <= $daysInMonth; $day++) {
            // Format the date as YYYY-MM-DD
            $date = sprintf("%04d-%02d-%02d", $year, $month, $day);
            
            // Calculate the power for the current date
            $power = $solarField->CalculatePowerDate($date);
            $monthlyPower += $power;
        }

        // Store the monthly power in the array
        $monthlyPowers[] = intval($monthlyPower);

        // Output the summary for the current month
        echo "Total Power for " . date("F", mktime(0, 0, 0, $month, 10)) . " " . $year . ": " . intval($monthlyPower) . " Wh<br>";
    }
}
?>

<!-- Chart.js container -->
<canvas id="monthlyPowerChart" width="400" height="200"></canvas>

<script>
    // Get the monthly power data from PHP
    var monthlyPowers = <?php echo json_encode($monthlyPowers); ?>;
    var ctx = document.getElementById('monthlyPowerChart').getContext('2d');
    var monthlyPowerChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            datasets: [{
                label: 'Monthly Power (Wh)',
                data: monthlyPowers,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
</script>

</body> 
</html>