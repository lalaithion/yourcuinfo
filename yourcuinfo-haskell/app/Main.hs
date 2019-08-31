{-# LANGUAGE OverloadedStrings #-}

module Main (main) where

import Control.Monad.IO.Class
import Control.Concurrent.Async
import Data.Aeson
import qualified Data.HashMap.Strict as M
import Data.Maybe
import Data.Proxy
import Data.Text (Text)
import qualified Data.Text as T
import qualified Data.Vector as V
import Network.HTTP.Req
import Control.Concurrent.MSem
import Control.Concurrent.Async
import Control.Concurrent (threadDelay)
import qualified Data.Traversable as T

(classesURL, classesOptions) = fromJust $ parseUrlHttps "https://classes.colorado.edu/api/?page=fose&route=search"
(detailsURL, detailsOptions) = fromJust $ parseUrlHttps "https://classes.colorado.edu/api/?page=fose&route=details"

semesterCodes :: [(Text, Text)]
semesterCodes = [ ("Spring", "1"), ("Summer", "4"), ("Fall", "7") ]

toArray = Array . V.fromList
toObject = Object . M.fromList

getClasses :: Text -> IO Value
getClasses semester_code = responseBody <$> runReq defaultHttpConfig (req
    POST
    classesURL
    (ReqBodyJson (toObject [
      ("other", toObject [("srcdb", String(semester_code))]),
      ("criteria", toArray [])
    ]))
    (jsonResponse :: Proxy (JsonResponse Value))
    classesOptions)

getDetails :: Text -> Text -> Text -> IO Value
getDetails semester_code class_code course_number = do
  responseBody <$> runReq defaultHttpConfig (req
    POST
    detailsURL
    (ReqBodyJson (toObject [
      ("group", String("code:" <> class_code)),
      ("key", String("crn:" <> course_number)),
      ("srcdb", String(semester_code)),
      ("matched", String("crn:" <> course_number))
    ]))
    (jsonResponse :: Proxy (JsonResponse Value))
    detailsOptions)

getDetailsFromResult :: Text -> Value -> IO Value
getDetailsFromResult semester_code (Object result) = case (M.lookup "code" result, M.lookup "crn" result) of
  (Just (String code), Just (String crn)) -> getDetails semester_code code crn
  _ -> pure Null
getDetailsFromResult _ _ = pure Null

mapPool :: T.Traversable t => Int -> (a -> IO b) -> t a -> IO (t b)
mapPool max f xs = do
    sem <- new max
    mapConcurrently (with sem . f) xs

main :: IO ()
main = do
  let year = "2019"
  let semester = "Fall"
  let semesterCode = "2" <> T.take 2 (T.drop 2 year) <> fromMaybe "1" (lookup semester semesterCodes)

  Object classes <- getClasses semesterCode
  
  results <- case M.lookup "results" classes of
    Just (Array v) -> Array <$> mapPool 50 (getDetailsFromResult semesterCode) v
    _ -> pure (toArray [])

  encodeFile "classes.json" classes
  encodeFile "results.json" results
