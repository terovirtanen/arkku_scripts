<!DOCTYPE html>
<html>
<body>

<h1>Forecast</h1>

<?php
date_default_timezone_set($timezone);

include_once '../login.php';
include_once '../Forecast.php';


$forecast = new Forecast();
$forecast->Initialize();
$forecast->GetFmiData();
$forecast->SetForecastPower();
$forecast->StoreData($conn);

$forecast->DailyPowerForecast(false);

$today = date("Y-m-d");
echo "Today<br>";
PrintData($forecast->GetSummaryDataByDate($conn, $today));

$tomorrow = date("Y-m-d", strtotime("+1 day"));
echo "Tomorrow<br>";
PrintData($forecast->GetSummaryDataByDate($conn, $tomorrow));

// print all data for today
PrintDayData($forecast->GetDataByDate($conn, $today));

$conn->close();

function PrintDayData($data) {
    if (empty($data)) {
        echo "No data available.<br>";
        return;
    }

    echo "<table border='1'>";
    echo "<tr>
            <th>Date</th>
            <th>Max Power (Wh)</th>
            <th>Forecast Power (Wh)</th>
            <th>Clouds</th>
            <th>Weather Symbol</th>
          </tr>";

    foreach ($data as $row) {
        echo "<tr>
                <td>" . $row['date'] . "</td>
                <td>" . $row['maxpower'] . "</td>
                <td>" . $row['forecastpower'] . "</td>
                <td>" . $row['clouds'] . "</td>
                <td>" . $row['weathersymbol'] . "</td>
              </tr>";
    }

    echo "</table>";}

function PrintData($data) {
    echo "&nbsp;&nbsp;Total Max Power:" . $data[0] . " Wh<br>";
    echo "&nbsp;Total Forecast Power: " . $data[1] . " Wh<br>";
}

?> 

</body>
</html>
