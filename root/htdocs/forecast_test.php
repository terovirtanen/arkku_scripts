<!DOCTYPE html>
<html>
<body>

<h1>Forecast</h1>

<?php
$timezone = "Europe/Helsinki";
date_default_timezone_set($timezone);

include_once '../Forecast.php';


$forecast = new Forecast();
$forecast->Initialize();
$forecast->GetFmiData(true);
$forecast->SetForecastPower();

$forecast->DailyPowerForecast(false);
$forecast->PrintForecastpoints();

$today = date("Y-m-d");
echo "Today<br>";


?> 

</body>
</html>
