# Evidence packet

Collected: 2026-10-21T07:41:50Z

## Prometheus — error runs (last 10 min)
```
{"status":"success","data":{"resultType":"vector","result":[{"metric":{"deployment_environment":"dev","exported_instance":"8d89592d-f738-43f4-8c74-4f6166cc16a5","exported_job":"sail-event-backend","instance":"otel-collector:8889","job":"otel-collector","otel_scope_name":"sail-event.pipeline","outcome":"error","service_instance_id":"8d89592d-f738-43f4-8c74-4f6166cc16a5","service_name":"sail-event-backend","service_version":"dev","telemetry_sdk_language":"python","telemetry_sdk_name":"opentelemetry","telemetry_sdk_version":"1.45.1","trigger":"manual"},"value":[1792568510.402,"28.04418620689655"]}]}}
```

## Loki — last 20 error lines
```
{"status":"success","data":{"resultType":"streams","result":[],"stats":{"summary":{"bytesProcessedPerSecond":0,"linesProcessedPerSecond":0,"totalBytesProcessed":0,"totalLinesProcessed":0,"execTime":0.020349,"queueTime":0.000207,"subqueries":0,"totalEntriesReturned":0,"splits":0,"shards":1,"totalPostFilterLines":0,"totalStructuredMetadataBytesProcessed":0},"querier":{"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":0,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}},"querierExecTime":0.006048},"ingester":{"totalReached":1,"totalChunksMatched":0,"totalBatches":1,"totalLinesSent":0,"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":84872,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}},"recvWaitTime":0.000522},"cache":{"chunk":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"index":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"result":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"statsResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"volumeResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"seriesResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"labelResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"instantMetricResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0}},"index":{"totalChunks":0,"postFilterChunks":0,"shardsDuration":0,"usedBloomFilters":false,"totalStreams":0,"chunkRefsLookupTime":0,"bloomFilterTime":0}}}}

```

## App health
```
{"status":"ok","commit":""}
```

## Recent commits
```
3d9f6b8 test: inject search-provider fault
c39c52c work: examiner 22/24, PR 92 merged, owner step for the last point
a348152 Merge pull request #92 from alexisdacquay/exam-final
ad56f19 incident-response: real-webhook reproduction, --dry-run, examiner frictions
815d76e work: examiner re-run 2 = 22/24
```

## Deployed version
```
unknown
```
