# Evidence packet

Collected: 2026-10-17T05:20:50Z

## Prometheus — error runs (last 10 min)
```
{"status":"success","data":{"resultType":"vector","result":[{"metric":{"deployment_environment":"dev","exported_instance":"b96ccd19-b88b-4790-8279-4bf2a1853ba4","exported_job":"sail-event-backend","instance":"otel-collector:8889","job":"otel-collector","otel_scope_name":"sail-event.pipeline","outcome":"error","service_instance_id":"b96ccd19-b88b-4790-8279-4bf2a1853ba4","service_name":"sail-event-backend","service_version":"dev","telemetry_sdk_language":"python","telemetry_sdk_name":"opentelemetry","telemetry_sdk_version":"1.45.1","trigger":"manual"},"value":[1792214450.197,"27.69221301807515"]},{"metric":{"deployment_environment":"dev","exported_instance":"b96ccd19-b88b-4790-8279-4bf2a1853ba4","exported_job":"sail-event-backend","instance":"otel-collector:8889","job":"otel-collector","otel_scope_name":"sail-event.pipeline","outcome":"error","service_instance_id":"b96ccd19-b88b-4790-8279-4bf2a1853ba4","service_name":"sail-event-backend","service_version":"dev","telemetry_sdk_language":"python","telemetry_sdk_name":"opentelemetry","telemetry_sdk_version":"1.45.1","trigger":"scheduled"},"value":[1792214450.197,"0"]}]}}
```

## Loki — last 20 error lines
```
{"status":"success","data":{"resultType":"streams","result":[],"stats":{"summary":{"bytesProcessedPerSecond":0,"linesProcessedPerSecond":0,"totalBytesProcessed":0,"totalLinesProcessed":0,"execTime":0.012655,"queueTime":0.000055,"subqueries":0,"totalEntriesReturned":0,"splits":0,"shards":1,"totalPostFilterLines":0,"totalStructuredMetadataBytesProcessed":0},"querier":{"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":0,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}},"querierExecTime":0.009332},"ingester":{"totalReached":1,"totalChunksMatched":0,"totalBatches":1,"totalLinesSent":0,"store":{"totalChunksRef":0,"totalChunksDownloaded":0,"chunksDownloadTime":0,"queryReferencedStructuredMetadata":false,"queryUsedV2Engine":false,"chunk":{"headChunkBytes":0,"headChunkLines":0,"decompressedBytes":0,"decompressedLines":0,"compressedBytes":0,"totalDuplicates":0,"postFilterLines":0,"headChunkStructuredMetadataBytes":0,"decompressedStructuredMetadataBytes":0},"chunkRefsFetchTime":121291,"congestionControlLatency":0,"pipelineWrapperFilteredLines":0,"dataobj":{"prePredicateDecompressedRows":0,"prePredicateDecompressedBytes":0,"prePredicateDecompressedStructuredMetadataBytes":0,"postPredicateRows":0,"postPredicateDecompressedBytes":0,"postPredicateStructuredMetadataBytes":0,"postFilterRows":0,"pagesScanned":0,"pagesDownloaded":0,"pagesDownloadedBytes":0,"pageBatches":0,"totalRowsAvailable":0,"totalPageDownloadTime":0}},"recvWaitTime":0.002911},"cache":{"chunk":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"index":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"result":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"statsResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"volumeResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"seriesResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"labelResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0},"instantMetricResult":{"entriesFound":0,"entriesRequested":0,"entriesStored":0,"bytesReceived":0,"bytesSent":0,"requests":0,"downloadTime":0,"queryLengthServed":0}},"index":{"totalChunks":0,"postFilterChunks":0,"shardsDuration":0,"usedBloomFilters":false,"totalStreams":0,"chunkRefsLookupTime":0,"bloomFilterTime":0}}}}

```

## App health
```
(health check failed)

```

## Recent commits
```
7318f2f test: inject scorer fault
5bc3eac S12: fix responder env and worktree cleanup for headless claude
3132250 S12: Makefile responder target, gitignore incidents, fix script perms
008f060 S12: task prompt, runbooks, test-incident
84840ff S12: responder, evidence collector, policy, schema
```

## Deployed version
```
unknown
```
