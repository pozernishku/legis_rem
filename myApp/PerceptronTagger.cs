using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Formatters.Binary;

namespace PartOfSpeechTagger
{
    public class PerceptronTagger
    {
        /*
         * Greedy Averaged Perceptron tagger, as implemented by Matthew Honnibal.
         * See more implementation details here:
         * http://honnibal.wordpress.com/2013/09/11/a-good-part-of-speechpos-tagger-in-about-200-lines-of-python/
         * :param load: Load the pickled model upon instantiation.
         */        

        public string[] START = { "-START-", "-START2-" };
        public string[] END = { "-END-", "-END2-" };
        public string PICKLE = "trontagger-0.1.0.pickle";
        public string AP_MODEL_LOC;

        public AveragedPerceptron model = new AveragedPerceptron();
        public Dictionary<string, string> tagDict = new Dictionary<string, string>();
        public HashSet<string> classes = new HashSet<string>();

        public PerceptronTagger(bool load=true)
        {
            // DONE.
            AP_MODEL_LOC = Path.Combine(".", PICKLE);

            if(load)
            {
                this.Load(this.AP_MODEL_LOC);
            }
        }

        public ArrayList Tag(string corpus, bool tokenize=false)
        {
            // DONE.
            // Tags a string `corpus`.
            // Assume untokenized corpus has \n between sentences and ' ' between words.
            // s_split = SentenceTokenizer().tokenize if tokenize else lambda t: t.split('\n')
            // w_split = WordTokenizer().tokenize if tokenize else lambda s: s.split()
            Func<string, string[]> sSplit = (string t) => t.Split('\n');
            Func<string, string[]> wSplit = (string s) => s.Split();

            string prev = this.START[0];
            string prev2 = this.START[1];
            ArrayList tokens = new ArrayList();

            foreach(string sentence in sSplit(corpus))
            {
                string[] words = wSplit(sentence);
                string[] context = new string[this.START.Length + words.Length + this.END.Length];
                this.START.CopyTo(context, 0);
                words.CopyTo(context, this.START.Length);
                this.END.CopyTo(context, this.START.Length + words.Length);
                for(int i = 0; i < words.Length; ++i)
                {
                    context[this.START.Length + i] = _Normalize(context[this.START.Length + i]);
                }

                for(int i = 0; i < words.Length; ++i)
                {
                    string word = words[i];
                    string tag;
                    bool isTag = this.tagDict.TryGetValue(word, out tag);
                    if(isTag == false)
                    {
                        Dictionary<string, int> features = this._GetFeatures(i, word, context, prev, prev2);
                        tag = this.model.Predict(features);
                    }
                    tokens.Add(new Tuple<string, string>(word, tag));
                    prev2 = prev;
                    prev = tag;
                }
            }

            return tokens;
        }

        public void Train(Tuple<string[], string[]>[] sentences, string saveLoc = null, int nrIter = 5)
        {
            // DONE.
            // Train a model from sentences, and save it at ``save_loc``. ``nr_iter``
            // controls the number of Perceptron training iterations.

            this._MakeTagdict(sentences);
            this.model.classes = this.classes;
            string prev = this.START[0];
            string prev2 = this.START[1];

            for (int iter_ = 0; iter_ < nrIter; ++iter_)
            {
                int c = 0;
                int n = 0;

                foreach (Tuple<string[], string[]> sentence in sentences)
                {
                    string[] words = sentence.Item1;
                    string[] tags = sentence.Item2;

                    string[] context = new string[this.START.Length + words.Length + this.END.Length];
                    this.START.CopyTo(context, 0);
                    words.CopyTo(context, this.START.Length);
                    this.END.CopyTo(context, this.START.Length + words.Length);
                    for (int i = 0; i < words.Length; ++i)
                    {
                        context[this.START.Length + i] = _Normalize(context[this.START.Length + i]);
                    }

                    for (int i = 0; i < words.Length; ++i)
                    {
                        string word = words[i];

                        string guess;
                        bool isGuess = this.tagDict.TryGetValue(word, out guess);
                        if (isGuess == false)
                        {
                            Dictionary<string, int> feats = this._GetFeatures(i, word, context, prev, prev2);
                            guess = this.model.Predict(feats);
                            this.model.Update(tags[i], guess, feats);
                        }

                        prev2 = prev;
                        prev = guess;
                        if (guess == tags[i]) c += 1;
                        n += 1;
                    }
                }

                Random rnd = new Random();
                sentences = sentences.OrderBy(sentence => rnd.Next()).ToArray();
                Console.WriteLine(string.Format("Iter {0}: {1}/{2}={3}", iter_, c, n, ((float)c) / n * 100));
            }
            this.model.AverageWeights();

            // Pickle as a binary file
            if (saveLoc != null)
                this.Save(saveLoc);

            return;
        }

        public void _MakeTagdict(Tuple<string[], string[]>[] sentences)
        {
            // DONE.
            // Make a tag dictionary for single-tag words.
            Dictionary<string, Dictionary<string, int>> counts = new Dictionary<string, Dictionary<string, int>>();
            foreach(Tuple<string[], string[]> sentence in sentences)
            {
                string[] words = sentence.Item1;
                string[] tags = sentence.Item2;

                for(int i = 0; i < words.Length; ++i)
                {
                    string word = words[i];
                    string tag = tags[i];

                    // counts[word][tag] += 1; // Default dict problem.

                    Dictionary<string, int> firstValue;
                    if (counts.TryGetValue(word, out firstValue) == false)
                    {
                        firstValue = new Dictionary<string, int>();
                        counts[word] = firstValue;
                    }

                    int secondValue;
                    if (counts[word].TryGetValue(tag, out secondValue) == false)
                    {
                        secondValue = 0;
                    }

                    counts[word][tag] = secondValue + 1;

                    this.classes.Add(tag);
                }
            }

            int freqThresh = 20;
            float ambiguityThresh = 0.97f;
            foreach(KeyValuePair<string, Dictionary<string, int>> pair in counts)
            {
                string word = pair.Key;
                Dictionary<string, int> tagFreqs = pair.Value;

                string tag = tagFreqs.Aggregate((x, y) => x.Value > y.Value ? x : y).Key;
                int mode = tagFreqs.Values.Max();

                int n = tagFreqs.Values.Sum();
                // Don't add rare words to the tag dictionary
                // Only add quite unambiguous words
                if(n >= freqThresh && (((float) mode) / n) >= ambiguityThresh)
                {
                    this.tagDict[word] = tag;
                }
            }
        }

        public string _Normalize(string word)
        {
            // Normalization used in pre-processing.
            // - All words are lower cased
            // - Digits in the range 1800 - 2100 are represented as !YEAR;
            // - Other digits are represented as !DIGITS
            if (word.Contains("-") && word[0] != '-')
            {
                return "!HYPHEN";
            }
            else if (int.TryParse(word, out int n) && word.Length == 4)
            {
                return "!YEAR";
            }
            else if(char.IsDigit(word[0]))
            {
                return "!DIGITS";
            }
            else
            {
                return word.ToLower();
            }
        }

        public Dictionary<string, int> _GetFeatures(int i, string word, string[] context, string prev, string prev2)
        {
            // Map tokens into a feature representation, implemented as a
            // {hashable: float} dict. If the features change, a new model must be
            // trained.
            i += this.START.Length;
            Dictionary<string, int> features = new Dictionary<string, int>();
            // It's useful to have a constant feature, which acts sort of like a prior.
            Add("bias");
            Add("i suffix", new string[] { word.Substring(Math.Max(0, word.Length - 3)) });
            Add("i pref1", new string[] { word.Substring(0, 1) });
            Add("i-1 tag", new string[] { prev });
            Add("i-2 tag", new string[] { prev2 });
            Add("i tag+i-2 tag", new string[] { prev, prev2 });
            Add("i word", new string[] { context[i] });
            Add("i-1 tag+i word", new string[] { prev, context[i] });
            Add("i-1 word", new string[] { context[i - 1] });
            Add("i-1 suffix", new string[] { context[i - 1].Substring(Math.Max(0, context[i - 1].Length - 3)) });
            Add("i-2 word", new string[] { context[i - 2] });
            Add("i+1 word", new string[] { context[i + 1] });
            Add("i+1 suffix", new string[] { context[i + 1].Substring(Math.Max(0, context[i + 1].Length - 3)) });
            Add("i+2 word", new string[] { context[i + 2] });

            return features;

            void Add(string name, string[] args=null)
            {
                ArrayList toArrayList;
                if(args != null)
                {
                    toArrayList = new ArrayList(args);
                }
                else
                {
                    toArrayList = new ArrayList();
                }

                toArrayList.Insert(0, name);

                string key = string.Join(" ", toArrayList.ToArray());

                int value;
                if(features.TryGetValue(key, out value) == false)
                {
                    value = 0;
                }

                features[key] = value + 1;
            }
        }

        public void Load(string loc)
        {
            // DONE.
            // Load a pickled model.
            Tuple<Dictionary<string, Dictionary<string, float>>, Dictionary<string, string>, HashSet<string>> wTdC;

            FileStream fs = new FileStream(loc, FileMode.Open);
            try
            {
                BinaryFormatter formatter = new BinaryFormatter();

                wTdC = (Tuple<Dictionary<string, Dictionary<string, float>>, Dictionary<string, string>, HashSet<string>>) formatter.Deserialize(fs);
            }
            catch (SerializationException e)
            {
                Console.WriteLine("Failed to deserialize. Reason: " + e.Message);
                throw;
            }
            finally
            {
                fs.Close();
            }

            this.model.weights = wTdC.Item1;
            this.tagDict = wTdC.Item2;
            this.classes = wTdC.Item3;

            this.model.classes = this.classes;

            return;
        }

        public void Save(string loc)
        {
            Tuple<Dictionary<string, Dictionary<string, float>>, Dictionary<string, string>, HashSet<string>> wTdC;
            wTdC = new Tuple<Dictionary<string, Dictionary<string, float>>, Dictionary<string, string>, HashSet<string>>(this.model.weights, this.tagDict, this.classes);

            FileStream fs = new FileStream(loc, FileMode.Create);

            BinaryFormatter formatter = new BinaryFormatter();
            try
            {
                formatter.Serialize(fs, wTdC);
            }
            catch (SerializationException e)
            {
                Console.WriteLine("Failed to serialize. Reason: " + e.Message);
                throw;
            }
            finally
            {
                fs.Close();
            }
        }
    }
}