<?php
function generate_signature($merchantCode, $merchantKey, $timestamp) {
    $data_to_hash = $merchantCode . $timestamp . $merchantKey;
    $signature = hash('sha256', $data_to_hash);
    return $signature;
}

// $timestamp = round(microtime(true) * 1000);

$merchantCode = 'SP87216';
$merchantKey = '30db2b938a585977643c9b3e37f63f65066c4756';
$timestamp = 12130928;
$signature = generate_signature($merchantCode, $merchantKey, $timestamp);
echo $signature;
?>
