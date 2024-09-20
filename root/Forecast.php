<?php
include_once 'SolarPower.php';

class Panels {
    public static $place = "koski_tl"; // fmi location name

    public static $panelTilt1 = 22; 
    public static $panelAzimuth1 = 90;
    public static $peakPower1 = 4050;

    public static $panelTilt2 = 22; 
    public static $panelAzimuth2 = -90;
    public static $peakPower2 = 4050;
}

class Forecast {
    private $solarField;
    private $latitude;
    private $longitude;

    private $forecastPoints = array();
    
    public function Initialize() {
        $this->solarField = new SolarFieldPower();
        $this->solarField->AddPanel(Panels::$panelTilt1, Panels::$panelAzimuth1, Panels::$peakPower1);
        $this->solarField->AddPanel(Panels::$panelTilt2, Panels::$panelAzimuth2, Panels::$peakPower2);

        $xmlRaw = file_get_contents('https://opendata.fmi.fi/wfs?service=WFS&version=2.0.0&request=getFeature&storedquery_id=fmi::forecast::edited::weather::scandinavia::point::timevaluepair&place=' . Panels::$place . '&parameters=middleandlowcloudcover&');
        $this->responsePosition($xmlRaw);
        $this->solarField->SetLocation($this->latitude, $this->longitude);
        
        $this->responseHandler($xmlRaw);
    }

    public function SetForecastPower($debug = false) {
        foreach ($this->forecastPoints as $forecastPoint) {
            $forecastPoint->maxPower = $this->solarField->CalculatePowerDatetime($forecastPoint->datetime, $debug);
        }
    }

    public function DailyPowerForecast($dailyPrinted = false) {
        // date -> power
        $summary = array();

        foreach ($this->forecastPoints as $forecastPoint) {
            $d = $forecastPoint->datetime->format('Y-m-d');

            if (!isset($summary[$d])) {
                $summary[$d] = 0;
            }

            $dayPower = $forecastPoint->ForecastPower();
            $summary[$d] += $dayPower;

            if ($dailyPrinted) {
                echo "  Forecast Solar Power on " . $forecastPoint->datetime->format('Y-m-d H:i:s') . " is : " . number_format($dayPower, 0) . " Wh<br>";
            }  
        }

        foreach ($summary as $date => $power) {
            // $d = new DateTime($date);
            echo "Forecast Solar Power on " . $date . " is : " . number_format($power, 0) . " Wh<br>";
        }
    }
    
    public function StoreData($conn) {
            // $sql_forecast_fmi_daily = "CREATE TABLE forecast_fmi_daily(
        //     id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
        //     date DATETIME NOT NULL UNIQUE,
        //     clouds INT,
        //     maxpower INT NOT NULL,
        //     forecastpower INT NOT NULL
        //     );";
        foreach ($this->forecastPoints as $forecastPoint) {
            $date = $forecastPoint->datetime->format('Y-m-d H:i:s');
            $clouds = $forecastPoint->cloud;
            $maxpower = $forecastPoint->maxPower;
            $forecastpower = $forecastPoint->ForecastPower();

            $sql = "INSERT INTO forecast_fmi_daily (date, clouds, maxpower, forecastpower)
            VALUES ('$date', '$clouds', '$maxpower', '$forecastpower')
            ON DUPLICATE KEY UPDATE 
            clouds = '$clouds', forecastpower = '$forecastpower'";
    
            if ($conn->query($sql) === TRUE) {
                // echo "New record created successfully";
            } else {
                echo "Error: " . $sql . "<br>" . $conn->error;
            }

        }
    }

    public function GetDataByDate($conn, $date) {
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

    private function responsePosition($response, $debug = false) {
    
        // Split the text into lines
        $lines = explode("\n", $response);
    
        // Define the regular expressions to match
        // <gml:pos>60.65000 23.15000 </gml:pos>
        $regexPos = '/<gml:pos>(.+)\s(.+)<\/gml:pos>/';
        foreach ($lines as $index => $line) {
            if (preg_match($regexPos, $line, $posMatch)) {
                if ($debug) echo "Lat:  " . $posMatch[1] . "\n";
                if ($debug) echo "Long: " . $posMatch[2] . "\n";
    
                $this->latitude = floatval($posMatch[1]);
                $this->longitude = floatval($posMatch[2]);
            }
        }
    }

    private function responseHandler($response, $debug = false) {
        // Split the text into lines
        $lines = explode("\n", $response);
    
        // Define the regular expressions to match
        $regexTime = '/<wml2:time>(.*)<\/wml2:time>/';
        $regexValue = '/<wml2:value>(.*)<\/wml2:value>/';
    
        // Loop through each line and process it
        foreach ($lines as $index => $line) {
            if (preg_match($regexTime, $line, $timeMatch)) {
                if ($debug) echo "Time: " . $timeMatch[1] . "\n";
    
                // value is in the next line
                if (isset($lines[$index + 1])) {
                    $nextLine = $lines[$index + 1];
                    if (preg_match($regexValue, $nextLine, $valueMatch)) {
                        if ($debug) echo "Value: " . $valueMatch[1] . "\n";

                        $cloud = floatval($valueMatch[1]);
                        $datetime = new DateTime($timeMatch[1]);

                        $this->forecastPoints[] = new ForecastPoint($datetime, $cloud);        

                    }
                }
            }
        }
    }
}

class ForecastPoint {
    public $datetime;
    public $cloud;
    public $maxPower;

    function __construct($datetime, $cloud) {
        
        $this->datetime = $datetime;
        $this->cloud = $cloud;
    }

    public function ForecastPower() {
        $cloudCover = 100 - $this->cloud;
        $cloudFix = 0;
        if ($this->cloud > 80) $cloudFix = 5;
        if ($this->cloud > 90) $cloudFix = 10;
        return $this->maxPower * (($cloudCover + $cloudFix) / 100);
    }
}
?>
