<?php
if (file_exists("../login_pc.php")) {
    include_once 'login_pc.php';
} else {
    include_once 'login_server.php';
}
?>
