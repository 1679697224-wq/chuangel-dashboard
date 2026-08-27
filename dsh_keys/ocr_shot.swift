import Foundation
import Vision
import AppKit

let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("ERR load image"); exit(1)
}
let W = CGFloat(cg.width), H = CGFloat(cg.height)
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hans", "en-US"]
req.usesLanguageCorrection = true
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try? handler.perform([req])
let obs = (req.results ?? []).sorted { a, b in
    let y1 = a.boundingBox.origin.y, y2 = b.boundingBox.origin.y
    if abs(y1 - y2) > 0.02 { return y1 > y2 }
    return a.boundingBox.origin.x < b.boundingBox.origin.x
}
for o in obs {
    let bb = o.boundingBox
    let x = Int(bb.origin.x * W), y = Int((1 - bb.origin.y - bb.height) * H)
    let w = Int(bb.width * W), h = Int(bb.height * H)
    if let t = o.topCandidates(1).first?.string {
        print("y=%4d x=%4d w=%4d h=%3d  %@" , y, x, w, h, t)
    }
}
