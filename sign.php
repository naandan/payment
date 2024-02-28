<?php
function generate_signature($merchantCode, $merchantKey, $timestamp) {
    $data_to_hash = $merchantCode . $timestamp . $merchantKey;
    $signature = hash('sha256', $data_to_hash);
    return $signature;
}

// $timestamp = round(microtime(true) * 1000);

$merchantCode = 'SP76238';
$merchantKey = '17ff92064f6f802dfa04ba5612bd129fe7be3a1d';
$timestamp = 12130928;
$signature = generate_signature($merchantCode, $merchantKey, $timestamp);
echo $signature;
?>
