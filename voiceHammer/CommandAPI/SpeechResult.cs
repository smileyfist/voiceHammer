using System;
using System.Collections.Generic;
using System.Text;

namespace CommandAPI
{
    //class used for the result of calling the speech API
    public class SpeechResult
    {
        public string RecognitionStatus { get; set; }
        public string Offset { get; set; }
        public string Duration { get; set; }
        public List<Nbest> NBest { get; set; }
    }
    //nested class in the result
    public class Nbest
    {
        public string Confidence { get; set; }
        public string Lexical { get; set; }
        public string ITN { get; set; }
        public string MaskedITN { get; set; }
        public string Display { get; set; }
    }
}
