<?php
// tests/SolarFieldPowerTest.php

require_once 'root/SolarPower.php';

use PHPUnit\Framework\TestCase;

// Set the default timezone to Finland
// date_default_timezone_set('Europe/Helsinki');
date_default_timezone_set('UTC');

class SolarFieldPowerTest extends TestCase {
    public function testSetLocation() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);

        $this->assertEquals(60.6531, $solarField->getLatitude() );
        $this->assertEquals(23.0500, $solarField->getLongitude());
    }

    public function testAddPanel() {
        $solarField = new SolarFieldPower();
        $solarField->AddPanel(22, 90, 4.05, 1.0);
        $solarField->AddPanel(22, -90, 4.05, 1.0);

        $this->assertCount(2, $solarField->getPanels());
        $this->assertInstanceOf(SolarPanel::class, $solarField->getPanels()[0]);
        $this->assertInstanceOf(SolarPanel::class, $solarField->getPanels()[1]);
    }

    public function testCalculatePowerDate() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);
        $solarField->AddPanel(22, 90, 4.05, 1.0);
        $solarField->AddPanel(22, -90, 4.05, 1.0);

        $power = $solarField->CalculatePowerDate('2023-05-18');

        $this->assertInternalType('numeric', $power);
        $this->assertGreaterThan(0, $power);
    }

    public function testCalculatePowerDatetime() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);
        $solarField->AddPanel(22, 90, 4.05, 1.0);
        $solarField->AddPanel(22, -90, 4.05, 1.0);

        $datetime = new DateTime('2023-05-18 12:00:00');
        $power = $solarField->CalculatePowerDatetime($datetime);

        $this->assertInternalType('numeric', $power);
        $this->assertGreaterThan(0, $power);
    }

    public function testCalculatePowerDatetime_panel90_0() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);
        $solarField->AddPanel(90, 0, 4, 1.0);

        $datetime = new DateTime('2023-06-25 11:00:00');
        $power = $solarField->CalculatePowerDatetime($datetime, true);

        $this->assertInternalType('numeric', $power);
        $this->assertGreaterThan(0, $power);
    }
    public function testCalculatePowerDatetime_panel38_0() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);
        $solarField->AddPanel(38, 0, 4, 1.0);

        $datetime = new DateTime('2023-06-25 11:00:00');
        $power = $solarField->CalculatePowerDatetime($datetime, true);

        $this->assertInternalType('numeric', $power);
        $this->assertGreaterThan(0, $power);
    }
    public function testCalculatePowerDatetime_panel22_90() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);
        $solarField->AddPanel(22, 90, 4, 1.0);

        $datetime = new DateTime('2023-06-25 11:00:00');
        $power = $solarField->CalculatePowerDatetime($datetime, true);

        $this->assertInternalType('numeric', $power);
        $this->assertGreaterThan(0, $power);
    }

    public function testPowerOutputThroughoutDay_Midsummer() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);
        $solarField->AddPanel(22, 90, 4.05, 1.0);
        $solarField->AddPanel(22, -90, 4.05, 1.0);

        $date = '2023-05-18';
        $timezoneUTC = new DateTimeZone('UTC');
        $timezoneHelsinki = new DateTimeZone('Europe/Helsinki');
        $startTime = new DateTime("$date 00:00:00", $timezoneUTC);
        $endTime = new DateTime("$date 23:59:59", $timezoneUTC);
        $interval = new DateInterval('PT5M');
        $times = [];
        $powers = [];

        for ($time = clone $startTime; $time <= $endTime; $time->add($interval)) {
            $power = $solarField->CalculatePowerDatetime($time);
            $time->setTimezone($timezoneHelsinki); // Convert to Helsinki timezone
            $times[] = $time->format('H:i');
            $time->setTimezone($timezoneUTC); // Reset to UTC for the next iteration
            $powers[] = $power;
        }

        // Save the data to a JSON file
        $data = [
            'times' => $times,
            'powers' => $powers
        ];
        file_put_contents('power_output_midsummer.json', json_encode($data));

        // Save the data to a JSON file
        // UTC + 2
        // Original reference data
        $data_ref_list = [
            ['time' => '05:00', 'power' => 0.05],
            ['time' => '05:30', 'power' => 0.21],
            ['time' => '06:00', 'power' => 0.55],
            ['time' => '06:30', 'power' => 1.26],
            ['time' => '07:00', 'power' => 1.72],
            ['time' => '08:00', 'power' => 2.37],
            ['time' => '09:00', 'power' => 3.04],
            ['time' => '12:00', 'power' => 5.00],
            ['time' => '13:00', 'power' => 5.23],
            ['time' => '13:30', 'power' => 5.27],
            ['time' => '14:00', 'power' => 5.23],
            ['time' => '15:00', 'power' => 4.89],
            ['time' => '17:00', 'power' => 3.57],
            ['time' => '19:00', 'power' => 2.23],
            ['time' => '19:30', 'power' => 1.92],
            ['time' => '20:00', 'power' => 1.59],
            ['time' => '20:30', 'power' => 1.2],
            ['time' => '21:00', 'power' => 0.8],
            ['time' => '21:30', 'power' => 0.38],
            ['time' => '22:00', 'power' => 0.02]
        ];

        // Convert list of key-value pairs to separate times and powers arrays
        $data_ref = ['times' => [], 'powers' => []];
        foreach ($data_ref_list as $entry) {
            $data_ref['times'][] = $entry['time'];
            $data_ref['powers'][] = $entry['power'];
        }

        file_put_contents('power_output_midsummer_ref.json', json_encode($data_ref));
       
    }

    public function testPowerOutputThroughoutDay_Autumn() {
        $solarField = new SolarFieldPower();
        $solarField->SetLocation(60.6531, 23.0500);
        $solarField->AddPanel(22, 90, 4.05, 1.0);
        $solarField->AddPanel(22, -90, 4.05, 1.0);

        $date = '2023-09-06';
        $timezoneUTC = new DateTimeZone('UTC');
        $timezoneHelsinki = new DateTimeZone('Europe/Helsinki');
        $startTime = new DateTime("$date 00:00:00", $timezoneUTC);
        $endTime = new DateTime("$date 23:59:59", $timezoneUTC);
        $interval = new DateInterval('PT5M');
        $times = [];
        $powers = [];

        for ($time = clone $startTime; $time <= $endTime; $time->add($interval)) {
            $power = $solarField->CalculatePowerDatetime($time);
            $time->setTimezone($timezoneHelsinki); // Convert to Helsinki timezone
            $times[] = $time->format('H:i');
            $time->setTimezone($timezoneUTC); // Reset to UTC for the next iteration
            $powers[] = $power;
        }

        // Save the data to a JSON file
        $data = [
            'times' => $times,
            'powers' => $powers
        ];
        file_put_contents('power_output_autumn.json', json_encode($data));

        // Save the data to a JSON file
        // UTC + 2
        // Original reference data
        $data_ref_list = [
            ['time' => '06:30', 'power' => 0.02], //5:30
            ['time' => '07:00', 'power' => 0.1],
            ['time' => '08:00', 'power' => 1.16],
            ['time' => '09:00', 'power' => 1.85],
            ['time' => '12:00', 'power' => 3.46],
            ['time' => '12:30', 'power' => 3.63],
            ['time' => '12:55', 'power' => 3.83],
            ['time' => '13:30', 'power' => 3.91],
            ['time' => '14:00', 'power' => 3.83],
            ['time' => '15:00', 'power' => 3.5],
            ['time' => '17:00', 'power' => 2.3],
            ['time' => '19:00', 'power' => 1.28],
            ['time' => '19:30', 'power' => 0.83],
            ['time' => '20:00', 'power' => 0.21],
            ['time' => '20:30', 'power' => 0.02]
        ];

        // Convert list of key-value pairs to separate times and powers arrays
        $data_ref = ['times' => [], 'powers' => []];
        foreach ($data_ref_list as $entry) {
            $data_ref['times'][] = $entry['time'];
            $data_ref['powers'][] = $entry['power'];
        }

        file_put_contents('power_output_autumn_ref.json', json_encode($data_ref));
       
    }
}