using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.IO;
using System.Net;
using System.Net.Http;

namespace CommandAPI
{
    public static class Commander
    {
        [FunctionName("Commander")]
        public static IActionResult Run([HttpTrigger(AuthorizationLevel.Function, "get", "post", Route = null)]
                                            HttpRequest req, ILogger log, ExecutionContext context)
        {
            log.LogInformation("Request received. Processing...");

            //add local settings which contains endpoints, keys etc
            var configuration = new ConfigurationBuilder()
             .SetBasePath(context.FunctionAppDirectory)
             .AddJsonFile("local.settings.json", true, true)
             .AddEnvironmentVariables()
             .Build();


            //pull out the audio from the request, if there is none, don't process further, send badrequest back
            var audio = GetAudioFromRequest(req);
            if (audio==null)
            {
                return new BadRequestObjectResult($"Request has empty body!!");
            }

            //there is audio in the request so continue to process. main logic in here.
            var result = ProcessRequest(configuration, audio, log);
            return result;
        }


        //read the body of the request and return it as byte array. if it can't do so, return null
        private static byte[] GetAudioFromRequest(HttpRequest req)
        {
            try
            {
                BinaryReader filereader = new BinaryReader(req.Body);
                byte[] byteArray = filereader.ReadBytes((int)req.Body.Length);
                filereader.Close();
                return byteArray;
            }
            catch (NotSupportedException)
            {
                return null;
            }
        }


        //main orchestrating method.
        //1. get token to be used for speech API call.
        //2. build request and send it to speech API.
        //3. call LUIS to get intent from speech result
        //4. based on intent return differnt status codes
        public static IActionResult ProcessRequest(IConfigurationRoot configuration, byte[] byteArray, ILogger log)
        {
            //Note! tokens last ten minutes and you shouldn't need to create a new one each time like I've done below.
            //This needs improvement.
            var token = GetSpeechToken(configuration, log);
            var request = BuildRequest(configuration, byteArray, token);
            var speechResult = MakeSpeechAPICall(configuration, request, log);

            if (speechResult == string.Empty)
            {
                return new StatusCodeResult((int)HttpStatusCode.NotFound);
            }

            var desiredIntent = FindIntentFromText(configuration, speechResult, log);

            if (desiredIntent == string.Empty)
            {
                return new StatusCodeResult((int)HttpStatusCode.NotFound);
            }
            log.LogInformation("desiredIntent:" + desiredIntent);

            switch (desiredIntent)
            {
                //you can add your own keywords here. Note, these will need to match what you've setup in LUIS
                //the raspberry pi will perform different actions based on these response codes.
                case "CombatReady":
                    return new StatusCodeResult((int)HttpStatusCode.OK);//200
                case "CoolDown":
                    return new StatusCodeResult((int)HttpStatusCode.Accepted);//202
                case "Ignite":
                    return new StatusCodeResult((int)HttpStatusCode.Created);//201
                case "MakeSandwich":
                    return new StatusCodeResult((int)HttpStatusCode.NoContent);//204
                default:
                    return new StatusCodeResult((int)HttpStatusCode.NotFound);//404
            }
        }

        private static string FindIntentFromText(IConfigurationRoot configuration, string speechResult, ILogger log)
        {
            //build request
            var endpoint = configuration["LUISEndpoint"];
            var uri = endpoint + speechResult;
            var request = HttpWebRequest.Create(uri);

            //hit LUIS
            log.LogInformation("time to call LUIS...");
            var response = (HttpWebResponse)request.GetResponse();

            log.LogInformation("response status:" + response.StatusCode);

            string responseText = string.Empty;
            using (var reader = new StreamReader(response.GetResponseStream()))
            {
                responseText = reader.ReadToEnd();
            }
            dynamic intentObject = JsonConvert.DeserializeObject(responseText);

            var requiredConfidence = decimal.Parse(configuration["RequiredConfidence"]);

            //check to see if the result coming back confidence level is low, if so return empty.
            if ((decimal)intentObject.topScoringIntent.score < requiredConfidence)
            {
                return string.Empty;
            }

            log.LogInformation($"{(string)intentObject.topScoringIntent.intent} " +
                                $"score of:{(string)intentObject.topScoringIntent.score}");
            //return matched intent (keyword) from LUIS for further processing
            return (string)intentObject.topScoringIntent.intent;
        }

        private static string MakeSpeechAPICall(IConfigurationRoot configuration, HttpWebRequest request, ILogger log)
        {
            log.LogInformation("time to call Speech....");
            string responseText;

            HttpWebResponse response = (HttpWebResponse)request.GetResponse();
            log.LogInformation("Speech result statuscode: " + response.StatusCode.ToString());

            //extra logic could be added here so that if 401 is return then make a new token?
            using (var reader = new StreamReader(response.GetResponseStream()))
            {
                responseText = reader.ReadToEnd();
            }
            var SpeechResponse = JsonConvert.DeserializeObject<SpeechResult>(responseText);
            var requiredConfidence = decimal.Parse(configuration["RequiredConfidence"]);

            //pull out the text from the result of the speech API call
            var textBackFromSpeechApi = SpeechResponse.NBest[0].Lexical;
            if (SpeechResponse.RecognitionStatus.Equals("Success") &&
                decimal.Parse(SpeechResponse.NBest[0].Confidence) > requiredConfidence)
            {
                log.LogInformation("result from speech was:" + textBackFromSpeechApi);
                return textBackFromSpeechApi;
            }
            log.LogInformation("Fail result from speech API!" + textBackFromSpeechApi);
            return string.Empty;
        }

        //create a request with all the required parts to call speech API
        private static HttpWebRequest BuildRequest(IConfigurationRoot configuration, byte[] byteArray, string token)
        {
            var endpoint = configuration["SpeechEndpoint"];

            var uri = endpoint + "?language=en-NZ&format=detailed";
            HttpWebRequest request = null;
            request = (HttpWebRequest)HttpWebRequest.Create(uri);
            request.Headers["Authorization"] = "Bearer " + token;
            request.Headers["Transfer-Encoding"] = "chunked";
            request.Headers["Expect"] = "100-continue";
            request.Headers["Accept"] = "application/json;text/xml";
            request.Accept = "application/json;text/xml";
            request.Method = "POST";
            request.ContentType = "audio/wav; codecs=audio/pcm; samplerate=16000";
            request.ProtocolVersion = HttpVersion.Version11;
            request.SendChunked = true;
            request.AllowWriteStreamBuffering = false;

            var st = request.GetRequestStream();
            st.Write(byteArray, 0, byteArray.Length);
            st.Close();

            return request;
        }

        //create a token which is used to call speech API.
        //Note. currently this is called with every request, but they last much longer. could be improved...
        private static string GetSpeechToken(IConfigurationRoot configuration, ILogger log)
        {
            string token;
            var endpoint = configuration["TokenEndpoint"];
            var speechKey = configuration["SpeechKey"];

            using (var client = new HttpClient())
            {
                client.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", speechKey);
                UriBuilder uriBuilder = new UriBuilder(endpoint);
                var result = client.PostAsync(uriBuilder.Uri.AbsoluteUri, null).Result;
                token = result.Content.ReadAsStringAsync().Result;
            }
            log.LogInformation("token grabbed! ");

            return token;
        }
    }
}
