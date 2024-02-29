<?php
function generate_signature($merchantCode, $merchantKey, $timestamp) {
    $data_to_hash = $merchantCode . $timestamp . $merchantKey;
    $signature = hash('sha256', $data_to_hash);
    return $signature;
}

// $timestamp = round(microtime(true) * 1000);

$merchantCode = 'SP24168';
$merchantKey = '73f8855dbda8d8eb5423752ef5c1b7e92b25a4a3';
$timestamp = 12130928;
$signature = generate_signature($merchantCode, $merchantKey, $timestamp);
echo $signature;
?>
