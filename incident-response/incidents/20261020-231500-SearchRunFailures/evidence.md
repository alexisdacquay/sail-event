# Evidence packet

Collected: 2026-10-20T23:15:00Z

## Prometheus — error runs (last 10 min)
```
{"status":"success","data":{"resultType":"vector","result":[]}}
```

## Loki — last 20 error lines
```
{"status":"success","data":{"resultType":"streams","result":[],"stats":{"summary":{"bytesProcessedPerSecond":0,"linesProcessedPerSecond":0,"totalBytesProcessed":0,"totalLinesProcessed":0,"execTime":0.016324,"queueTime":0.00045,"subqueries":0,"totalEntriesReturned":0,"splits":0,"shards":1,"totalPostFilterLines":0,"totalStructuredMetadataBytesProcessed":0},"querier":{"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":0,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}},"querierExecTime":0.007585},"ingester":{"totalReached":1,"totalChunksMatched":0,"totalBatches":1,"totalLinesSent":0,"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":218184,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}},"recvWaitTime":0.002225},"cache":{"chunk":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"index":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"result":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"statsResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"volumeResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"seriesResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"labelResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"instantMetricResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0}},"index":{"totalChunks":0,"postFilterChunks":0,"shardsDuration":0,"usedBloomFilters":false,"totalStreams":0,"chunkRefsLookupTime":0,"bloomFilterTime":0}}}}

```

## App health
```
(health check failed)

```

## Recent commits
```
9158a3c test: inject search-provider fault
c9b1d74 fix responder incidents dir and allowlist
2a8ac5e incident-response: reproduction works on the current code; fresh recorded incident; fix.diff
deb3ce5 work: examiner report 17/24 and the fix plan
3dbff42 Merge pull request #88 from alexisdacquay/review-fixes
```

## Deployed version
```
unknown
```
