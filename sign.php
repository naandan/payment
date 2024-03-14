<?php
function generate_signature($merchantCode, $merchantKey, $timestamp) {
    $data_to_hash = $merchantCode . $timestamp . $merchantKey;
    $signature = hash('sha256', $data_to_hash);
    return $signature;
}

// $timestamp = round(microtime(true) * 1000);

$merchantCode = 'SP73845';
$merchantKey = '7c77f189df1e647d1ff0baf5e0c6c1d601f68c2d';
$timestamp = 12130928;
$signature = generate_signature($merchantCode, $merchantKey, $timestamp);
echo $signature;
?>
