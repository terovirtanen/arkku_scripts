<?php
include_once '../login.php';

date_default_timezone_set($timezone);

// echo "Tomorrow<br>";
$tomorrow = date("Y-m-d", strtotime("+1 day"));
$summary_res_tomorrow = GetForecastPower($tomorrow);
$conn->close();

$data = array("powerMax" => $summary_res_tomorrow[0], "powerForecast" => $summary_res_tomorrow[1]);
header("Content-Type: application/json");
echo json_encode($data);

// https://stackoverflow.com/questions/63206951/how-to-take-summary-from-a-sql-data-table-using-sql-query
function GetForecastPower($date) {
    global $conn;
    // echo "Date: " . $date . "<br>"; 
    $sql = "SELECT sum(maxpower) as totalMaxPower, sum(forecastpower) as totalForecastPower FROM forecast_fmi_daily WHERE date LIKE '$date%'";
    $result = $conn->query($sql);

    if ($result->num_rows > 0) {
        $totalMaxPower = 0;
        $totalForecastPower = 0;
        while($row = $result->fetch_assoc()) {
            $totalMaxPower += $row["totalMaxPower"];
            $totalForecastPower += $row["totalForecastPower"];
        }

        return array($totalMaxPower, $totalForecastPower);
    } 
    else {
        return array(-1,-1);
    }
}
