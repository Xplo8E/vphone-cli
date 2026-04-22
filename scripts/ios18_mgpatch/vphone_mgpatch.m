#import <Foundation/Foundation.h>
#import <sys/stat.h>
#import <unistd.h>

static NSString *const kCachePath = @"/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist";
static NSString *const kAltCachePath = @"/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist";
static NSString *const kSentinelPath = @"/private/var/root/.vphone_mobilegestalt_patched";

static NSString *ResolveCachePath(void) {
    NSFileManager *fm = [NSFileManager defaultManager];
    if ([fm fileExistsAtPath:kCachePath]) return kCachePath;
    if ([fm fileExistsAtPath:kAltCachePath]) return kAltCachePath;
    return kCachePath;
}

static BOOL PatchCache(NSString *path, NSError **error) {
    NSData *input = [NSData dataWithContentsOfFile:path options:0 error:error];
    if (!input) return NO;

    NSPropertyListFormat format = NSPropertyListBinaryFormat_v1_0;
    id root = [NSPropertyListSerialization propertyListWithData:input options:NSPropertyListMutableContainersAndLeaves format:&format error:error];
    if (![root isKindOfClass:[NSMutableDictionary class]]) {
        if (error) {
            *error = [NSError errorWithDomain:@"vphone_mgpatch" code:1 userInfo:@{NSLocalizedDescriptionKey: @"MobileGestalt root plist is not a dictionary"}];
        }
        return NO;
    }

    NSMutableDictionary *plist = (NSMutableDictionary *)root;
    id cacheExtra = plist[@"CacheExtra"];
    if (![cacheExtra isKindOfClass:[NSMutableDictionary class]]) {
        cacheExtra = [NSMutableDictionary dictionary];
        plist[@"CacheExtra"] = cacheExtra;
    }
    ((NSMutableDictionary *)cacheExtra)[@"DeviceClassNumber"] = @1;

    NSData *output = [NSPropertyListSerialization dataWithPropertyList:plist format:NSPropertyListBinaryFormat_v1_0 options:0 error:error];
    if (!output) return NO;

    NSString *tmp = [path stringByAppendingString:@".vphone_tmp"];
    NSString *bak = [path stringByAppendingString:@".vphone_bak"];
    NSFileManager *fm = [NSFileManager defaultManager];
    if (![fm fileExistsAtPath:bak]) {
        [fm copyItemAtPath:path toPath:bak error:nil];
    }
    if (![output writeToFile:tmp options:NSDataWritingAtomic error:error]) return NO;
    chmod([tmp fileSystemRepresentation], 0644);
    chown([tmp fileSystemRepresentation], 501, 501);
    [fm removeItemAtPath:path error:nil];
    if (![fm moveItemAtPath:tmp toPath:path error:error]) return NO;
    chmod([path fileSystemRepresentation], 0644);
    chown([path fileSystemRepresentation], 501, 501);
    return YES;
}

int main(int argc, char **argv) {
    @autoreleasepool {
        NSFileManager *fm = [NSFileManager defaultManager];
        NSString *path = nil;
        for (int i = 0; i < 180; i++) {
            path = ResolveCachePath();
            if ([fm fileExistsAtPath:path]) break;
            sleep(1);
        }

        path = ResolveCachePath();
        if (![fm fileExistsAtPath:path]) {
            NSLog(@"[vphone_mgpatch] MobileGestalt cache not found after wait");
            return 2;
        }

        NSError *error = nil;
        if (!PatchCache(path, &error)) {
            NSLog(@"[vphone_mgpatch] patch failed for %@: %@", path, error);
            return 1;
        }

        NSString *stamp = [NSString stringWithFormat:@"patched DeviceClassNumber=1 at %@\n", [NSDate date]];
        [stamp writeToFile:kSentinelPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
        chmod([kSentinelPath fileSystemRepresentation], 0644);
        NSLog(@"[vphone_mgpatch] patched %@", path);
        return 0;
    }
}
