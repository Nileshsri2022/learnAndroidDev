package eu.tutorials.myshoppinglistapp

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.create

object RetrofitClient {
    private const val BASE_URL = "https://maps.googleapis.com/"

    fun create(): GeocodingApiService{
        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        return  retrofit.create(GeocodingApiService::class.java)
    }
}