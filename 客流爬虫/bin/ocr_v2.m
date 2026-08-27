#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
#import <Vision/Vision.h>

// 用法: ocr_v2 <图片路径> [correction:0|1] [level:0|1]
int main(int argc, const char * argv[]) {
    @autoreleasepool {
        if (argc < 2) { printf("usage: ocr_v2 path [useCorrection] [level]\n"); return 1; }
        NSString *path = [NSString stringWithUTF8String:argv[1]];
        BOOL useCorrection = argc > 2 ? atoi(argv[2]) : 1;
        NSInteger level = argc > 3 ? atoi(argv[3]) : 0; // 0 accurate, 1 fast

        NSImage *img = [[NSImage alloc] initWithContentsOfFile:path];
        if (!img) { printf("ERR load\n"); return 1; }
        CGImageRef cg = [img CGImageForProposedRect:NULL context:nil hints:nil];
        if (!cg) { printf("ERR cg\n"); return 1; }

        VNRecognizeTextRequest *req = [[VNRecognizeTextRequest alloc] init];
        req.recognitionLevel = level == 1 ? VNRequestTextRecognitionLevelFast : VNRequestTextRecognitionLevelAccurate;
        req.recognitionLanguages = @[@"zh-Hans", @"en-US"];
        req.usesLanguageCorrection = useCorrection;

        VNImageRequestHandler *handler = [[VNImageRequestHandler alloc] initWithCGImage:cg options:@{}];
        NSError *err = nil;
        [handler performRequests:@[req] error:&err];
        if (err) { printf("ERR %s\n", err.localizedDescription.UTF8String); return 1; }

        NSArray<VNRecognizedTextObservation *> *results = req.results;
        NSMutableArray *lines = [NSMutableArray array];
        for (VNRecognizedTextObservation *obs in results) {
            VNRecognizedText *top = [obs topCandidates:1].firstObject;
            if (top.string) [lines addObject:top.string];
        }
        // 按 y 从上到下、x 从左到右排序
        NSArray *sorted = [results sortedArrayUsingComparator:^NSComparisonResult(VNRecognizedTextObservation *a, VNRecognizedTextObservation *b) {
            CGFloat ya = a.boundingBox.origin.y, yb = b.boundingBox.origin.y;
            if (fabs(ya - yb) > 0.02) return ya > yb ? NSOrderedAscending : NSOrderedDescending;
            return a.boundingBox.origin.x < b.boundingBox.origin.x ? NSOrderedAscending : NSOrderedDescending;
        }];
        for (VNRecognizedTextObservation *obs in sorted) {
            VNRecognizedText *top = [obs topCandidates:1].firstObject;
            if (top.string) printf("%s\n", top.string.UTF8String);
        }
        (void)lines;
    }
    return 0;
}
