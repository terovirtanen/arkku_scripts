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
$forecast->SetForecastPower();
$forecast->StoreData($conn);

$forecast->DailyPowerForecast(false);

$today = date("Y-m-d");
echo "Today<br>";
PrintData($forecast->GetDataByDate($conn, $today));

$tomorrow = date("Y-m-d", strtotime("+1 day"));
echo "Tomorrow<br>";
PrintData($forecast->GetDataByDate($conn, $tomorrow));

$conn->close();

function PrintData($data) {
    echo "&nbsp;&nbsp;Total Max Power:" . $data[0] . " Wh<br>";
    echo "&nbsp;Total Forecast Power: " . $data[1] . " Wh<br>";
}

?> 

</body>
</html>
