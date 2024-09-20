<?php
class SolarFieldPower {
    public $latitude; 
    public $longitude;
    
    private $panels = array();

    public function SetLocation($latitude, $longitude) {
        $this->$latitude = $latitude;
        $this->$longitude = $longitude;
        // set lat long to SolarPower
        SolarPower::Initialize($this->$latitude, $this->$longitude);
    }
    
    public function AddPanel($panelTilt, $panelAzimuth, $peakPower) {
        $this->panels[] = new SolarPanel($panelTilt, $panelAzimuth, $peakPower);        
    }

    // summary on date
    public function CalculatePowerDate($date) {
        $powerSummary = 0;
    
        // Ensure the date is in the correct format
        $date = new DateTime($date);
        // Loop through each hour from 00:00 to 23:00
        for ($hour = 0; $hour < 24; $hour++) {
            // Clone the date object to avoid modifying the original date
            $currentHour = clone $date;
            $currentHour->setTime($hour, 0, 0);

            $powerSummary += $this->CalculatePowerDatetime($currentHour);
        }
    
        return $powerSummary; // Add this line to return the power summary
    }

    // summary on date and time
    public function CalculatePowerDatetime($datetime, $debug = false) {
        $powerSummary = 0;

        foreach ($this->panels as $panel) {
            $powerSummary += $panel->Power($datetime, $debug);
        }

        return $powerSummary;
       
    }
}

class SolarPanel {
    public $panelTilt;
    public $panelAzimuth;
    public $peakPower;

    function __construct($panelTilt, $panelAzimuth, $peakPower) {
        $this->panelTilt = $panelTilt;
        $this->panelAzimuth = $panelAzimuth;
        $this->peakPower = $peakPower;
    }

    function Power($datetime, $debug = false) {
        return SolarPower::CalculateSolarPower($datetime, $this->panelTilt, $this->panelAzimuth, $this->peakPower, $debug);
    }

}


class SolarPower {
    public static $latitude; 
    public static $longitude;

    // public $panelTilt; // panel tilt 1:2,5
    // public $peakPower; = 8100; // Peak power of the panel in watts
    public static $panelEfficiency = 1.00; // Assume the panel efficiency is 100%


    // $power = calculateSolarPowerSummary($time, $debug);
    public static function Initialize($latitude, $longitude) {
        self::$latitude = $latitude;
        self::$longitude = $longitude;
    }

    // function calculateSolarPowerSummary($date, $debug = false) {
    //     if ($debug) echo "Date: " . $date->format('Y-m-d H:i:s') . "\n";

    //     // East-facing panels
    //     $eastAzimuth = -90; // East direction
    //     $eastPower = calculateSolarPower($date, $GLOBALS['panelTilt'], $eastAzimuth, $GLOBALS['peakPower'] / 2, $debug);

    //     // West-facing panels
    //     $westAzimuth = 90; // West direction
    //     $westPower = calculateSolarPower($date, $GLOBALS['panelTilt'], $westAzimuth, $GLOBALS['peakPower'] / 2, $debug);

    //     $totalPower = $eastPower + $westPower;
    //     if ($debug) echo "  Estimated Total Power: " . number_format($totalPower, 2) . " W\n";
    //     if ($debug) echo "\n";
    //     return $totalPower;
    // }

    public static function CalculateSolarPower($date, $panelTilt, $panelAzimuth, $peakPower, $debug = false) {
        $sunPosition = self::getSunPosition(self::$latitude, self::$longitude, $date, $debug); // date is UTC time

        $incidentAngle = self::calculateIncidentAngle($sunPosition['altitude'], $panelTilt, $panelAzimuth, $sunPosition['azimuth'], $debug);

        $cos = 1 - cos(deg2rad($incidentAngle));
        $sin = sin(deg2rad($incidentAngle));
        if ($debug) {
            echo "  incidentAngle: " . number_format($incidentAngle, 2) . "°\n";
        }

        // Adjustments based on incident angle
        $fix = 1.00;
        if ($incidentAngle < 35) { $fix = 0.80; }
        if ($incidentAngle < 25) { $fix = 0.60; }
        if ($incidentAngle > 60) { $fix = 0.92; }
        if ($incidentAngle > 70) { $fix = 0.85; }

        $maxIncidentAngle = self::$latitude;
        $fixFactory = 1 / (1 - cos(deg2rad($maxIncidentAngle)));
        $power = $incidentAngle < 1 ? 0 : $peakPower * $fix * self::$panelEfficiency * $fixFactory * (1 - cos(deg2rad($incidentAngle)));

        if ($debug) {
            echo "  power: " . number_format($power, 2) . " W\n";
        }

        return $power > 0 ? $power : 0;
    }

    private static function calculateIncidentAngle($sunAltitude, $panelTilt, $panelAzimuth, $sunAzimuth, $debug = false) {
        $azMin = -90 + $panelAzimuth;
        $azMax = 90 + $panelAzimuth;
        $AzimuthDirection = 1; // Sun shines from the front 1 or back -1
        if ($sunAzimuth < $azMin || $sunAzimuth > $azMax) {
            $AzimuthDirection = -1;
        }
        if ($sunAltitude <= 0) { // Check if the Sun is above the horizon
            return 0;
        }

        // Incident angle
        $tiltAngle = ($AzimuthDirection * $panelTilt) + $sunAltitude;

        // If the panel's incident angle is negative, it does not produce energy
        if ($tiltAngle < 0) {
            return 0;
        }

        return $tiltAngle;
    }

    private static function getSunPosition($latitude, $longitude, $date, $debug = false) {
        $sunPosition = SunCalc::getPosition($date, $latitude, $longitude);
        $azimuth = rad2deg($sunPosition['azimuth']);
        $altitude = rad2deg($sunPosition['altitude']);

        if ($debug) {
            echo "Date: " . $date->format('Y-m-d H:i:s') . "\n";
            echo "  Azimuth: " . $sunPosition['azimuth'] . "°\n";
            echo "  Azimuth: " . number_format($azimuth, 2) . "°\n";
            echo "  Altitude: " . number_format($altitude, 2) . "°\n";
        }

        return ['azimuth' => $azimuth, 'altitude' => $altitude];
    }
}

// SunCalc class from suncalc.js
class SunCalc {
    private static $PI = M_PI;
    private static $rad = M_PI / 180;
    private static $dayMs = 60 * 60 * 24;
    private static $J1970 = 2440588;
    private static $J2000 = 2451545;
    private static $e = 23.4397 * (M_PI / 180); // obliquity of the Earth

    public static function toJulian($date) {
        return $date->getTimestamp() / self::$dayMs - 0.5 + self::$J1970;
    }

    public static function fromJulian($j) {
        return new DateTime('@' . (($j + 0.5 - self::$J1970) * self::$dayMs / 1000));
    }

    public static function toDays($date) {
        return self::toJulian($date) - self::$J2000;
    }

    public static function rightAscension($l, $b) {
        return atan2(sin($l) * cos(self::$e) - tan($b) * sin(self::$e), cos($l));
    }

    public static function declination($l, $b) {
        return asin(sin($b) * cos(self::$e) + cos($b) * sin(self::$e) * sin($l));
    }

    public static function azimuth($H, $phi, $dec) {
        return atan2(sin($H), cos($H) * sin($phi) - tan($dec) * cos($phi));
    }

    public static function altitude($H, $phi, $dec) {
        return asin(sin($phi) * sin($dec) + cos($phi) * cos($dec) * cos($H));
    }

    public static function siderealTime($d, $lw) {
        return self::$rad * (280.16 + 360.9856235 * $d) - $lw;
    }

    public static function astroRefraction($h) {
        if ($h < 0) $h = 0;
        return 0.0002967 / tan($h + 0.00312536 / ($h + 0.08901179));
    }

    public static function solarMeanAnomaly($d) {
        return self::$rad * (357.5291 + 0.98560028 * $d);
    }

    public static function eclipticLongitude($M) {
        $C = self::$rad * (1.9148 * sin($M) + 0.02 * sin(2 * $M) + 0.0003 * sin(3 * $M));
        $P = self::$rad * 102.9372;
        return $M + $C + $P + self::$PI;
    }

    public static function sunCoords($d) {
        $M = self::solarMeanAnomaly($d);
        $L = self::eclipticLongitude($M);
        return [
            'dec' => self::declination($L, 0),
            'ra' => self::rightAscension($L, 0)
        ];
    }

    public static function getPosition($date, $lat, $lng) {
        $lw = self::$rad * -$lng;
        $phi = self::$rad * $lat;
        $d = self::toDays($date);

        $c = self::sunCoords($d);
        $H = self::siderealTime($d, $lw) - $c['ra'];
        return [
            'azimuth' => self::azimuth($H, $phi, $c['dec']),
            'altitude' => self::altitude($H, $phi, $c['dec'])
        ];
    }
}

?> 
