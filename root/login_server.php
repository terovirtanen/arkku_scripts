<?php
// $username, $password
include_once 'credentials.php';

$servername = "localhost";
$dbname = "132_oma"; 
$timezone = "Europe/Helsinki";
$datatable = "boiler";

$forecast_daily_table = "forecast_fmi_daily";

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);
// Check connection
if (!$conn) {
    die('Could not connect: ' . mysqli_error($conn));
}

// create tables to forecast
if ($conn){
    try {
        // $sql_drop_table = "DROP TABLE forecast_fmi_daily;";
        // if(mysqli_query($conn,$sql_drop_table) === TRUE) {
        //     // echo "Created sql_forecast_fmi_daily table";
        // } 

        $sql_forecast_fmi_daily = "CREATE TABLE IF NOT EXISTS forecast_fmi_daily(
            id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
            date DATETIME NOT NULL UNIQUE,
            clouds INT,
            maxpower INT NOT NULL,
            forecastpower INT NOT NULL
            );";
        if(mysqli_query($conn,$sql_forecast_fmi_daily) === TRUE) {
            // echo "Created sql_forecast_fmi_daily table";
        } 

        // else{
        //     echo "forecast_fmi table already exists";
        // }
    }
    //catch exception
    catch(Exception $e) {
        echo 'Message: ' .$e->getMessage();
    }
}
?>
